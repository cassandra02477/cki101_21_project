from google.cloud import storage
from flask import Flask, request, jsonify, render_template_string
import pymysql
import os

app = Flask(__name__)


DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 8625))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "cass123")
DB_NAME = os.environ.get("DB_NAME", "cki101_db")

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                age INT NOT NULL
            )
        """)
    conn.commit()
    conn.close()

HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>用戶管理系統</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
        h1 { color: #333; }
        input { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
        button { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-add { background: #4CAF50; color: white; }
        .btn-delete { background: #f44336; color: white; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #f5f5f5; }
        tr:hover { background: #f9f9f9; }
        .msg { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { background: #dff0d8; color: #3c763d; }
        .error { background: #f2dede; color: #a94442; }
    </style>
</head>
<body>
    <h1>用戶管理系統</h1>

    <h2>新增用戶</h2>
    <input type="text" id="name" placeholder="姓名">
    <input type="number" id="age" placeholder="年紀">
    <button class="btn-add" onclick="addUser()">新增</button>
    <div id="msg"></div>

    <h2>用戶列表</h2>
    <button onclick="loadUsers()">重新整理</button>
    <table>
        <thead>
            <tr><th>ID</th><th>姓名</th><th>年紀</th><th>操作</th></tr>
        </thead>
        <tbody id="user-list"></tbody>
    </table>

    <script>
        async function loadUsers() {
            const res = await fetch('/user');
            const users = await res.json();
            const tbody = document.getElementById('user-list');
            tbody.innerHTML = '';
            users.forEach(u => {
                tbody.innerHTML += `
                    <tr>
                        <td>${u.id}</td>
                        <td>${u.name}</td>
                        <td>${u.age}</td>
                        <td><button class="btn-delete" onclick="deleteUser(${u.id})">刪除</button></td>
                    </tr>`;
            });
        }

        async function addUser() {
            const name = document.getElementById('name').value;
            const age = document.getElementById('age').value;
            if (!name || !age) {
                showMsg('請填寫姓名和年紀', 'error');
                return;
            }
            const res = await fetch('/user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, age: parseInt(age) })
            });
            const data = await res.json();
            showMsg(data.message, 'success');
            document.getElementById('name').value = '';
            document.getElementById('age').value = '';
            loadUsers();
        }

        async function deleteUser(id) {
            if (!confirm('確定要刪除嗎？')) return;
            const res = await fetch('/user/' + id, { method: 'DELETE' });
            const data = await res.json();
            showMsg(data.message, 'success');
            loadUsers();
        }

        function showMsg(text, type) {
            const msg = document.getElementById('msg');
            msg.className = 'msg ' + type;
            msg.textContent = text;
            setTimeout(() => msg.textContent = '', 3000);
        }

        loadUsers();
    </script>
</body>
</html>
"""


@app.route("/user")
def index():
    return render_template_string(HTML)

@app.route("/user", methods=["POST"])
def create_user():
    data = request.get_json()
    name = data.get("name")
    age = data.get("age")
    if not name or not age:
        return jsonify({"error": "name 和 age 為必填"}), 400
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO users (name, age) VALUES (%s, %s)", (name, age))
    conn.commit()
    conn.close()
    return jsonify({"message": "新增成功"}), 201

@app.route("/user", methods=["GET"])
def get_users():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
    conn.close()
    return jsonify(users)

@app.route("/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "找不到用戶"}), 404
    return jsonify(user)

@app.route("/user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "刪除成功"})





GCP_PAGE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>GCP Storage 瀏覽器</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
        h1 { color: #333; }
        input { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; width: 300px; }
        button { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; background: #4285F4; color: white; }
        button:hover { background: #357ABD; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #f5f5f5; }
        tr:hover { background: #f9f9f9; }
        .msg { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .error { background: #f2dede; color: #a94442; }
        .bucket-btn { background: #34A853; margin: 3px; padding: 6px 12px; font-size: 13px; }
        .back-btn { background: #888; margin: 3px; padding: 6px 12px; font-size: 13px; }
    </style>
</head>
<body>
    <h1>GCP Cloud Storage 瀏覽器</h1>

    <h2>輸入 Project ID</h2>
    <input type="text" id="project-id" placeholder="例如：cki101-21-project">
    <button onclick="listBuckets()">查詢 Buckets</button>
    <div id="msg"></div>

    <div id="bucket-area"></div>
    <div id="file-area"></div>

    <script>
        let currentProject = '';

        async function listBuckets() {
            const projectId = document.getElementById('project-id').value.trim();
            if (!projectId) { showMsg('請輸入 Project ID'); return; }
            currentProject = projectId;

            const res = await fetch('/gcp/buckets?project_id=' + projectId);
            const data = await res.json();

            if (data.error) { showMsg(data.error); return; }

            const area = document.getElementById('bucket-area');
            if (data.buckets.length === 0) {
                area.innerHTML = '<p>此專案沒有 Bucket</p>';
                return;
            }

            let html = '<h2>Bucket 列表</h2>';
            data.buckets.forEach(b => {
                html += `<button class="bucket-btn" onclick="listFiles('${b}')">${b}</button>`;
            });
            area.innerHTML = html;
            document.getElementById('file-area').innerHTML = '';
        }

        async function listFiles(bucket) {
            const res = await fetch('/gcp/files?bucket=' + bucket);
            const data = await res.json();

            if (data.error) { showMsg(data.error); return; }

            const area = document.getElementById('file-area');
            let html = `<h2>📂 ${bucket} 的檔案</h2>`;
            html += `<button class="back-btn" onclick="document.getElementById('file-area').innerHTML=''">← 返回</button>`;

            if (data.files.length === 0) {
                html += '<p>此 Bucket 沒有檔案</p>';
            } else {
                html += '<table><thead><tr><th>檔案名稱</th><th>大小</th><th>最後更新</th></tr></thead><tbody>';
                data.files.forEach(f => {
                    html += `<tr><td>${f.name}</td><td>${f.size}</td><td>${f.updated}</td></tr>`;
                });
                html += '</tbody></table>';
            }
            area.innerHTML = html;
        }

        function showMsg(text) {
            const msg = document.getElementById('msg');
            msg.className = 'msg error';
            msg.textContent = text;
            setTimeout(() => msg.textContent = '', 4000);
        }
    </script>
</body>
</html>
"""

@app.route("/gcp")
def gcp_page():
    return render_template_string(GCP_PAGE)

@app.route("/gcp/buckets")
def list_buckets():
    project_id = request.args.get("project_id")
    if not project_id:
        return jsonify({"error": "請提供 project_id"}), 400
    try:
        client = storage.Client(project=project_id)
        buckets = [b.name for b in client.list_buckets()]
        return jsonify({"buckets": buckets})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/gcp/files")
def list_files():
    bucket_name = request.args.get("bucket")
    if not bucket_name:
        return jsonify({"error": "請提供 bucket 名稱"}), 400
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blobs = client.list_blobs(bucket_name)
        files = [{
            "name": b.name,
            "size": f"{b.size / 1024:.1f} KB" if b.size else "0 KB",
            "updated": b.updated.strftime("%Y-%m-%d %H:%M") if b.updated else ""
        } for b in blobs]
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)