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

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)