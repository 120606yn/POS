import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Response
try:
    import pymysql
    import pymysql.cursors
    USE_PYMYSQL = True
except ImportError:
    import mysql.connector
    from mysql.connector import Error
    USE_PYMYSQL = False
from werkzeug.security import generate_password_hash, check_password_hash
print(generate_password_hash("123456"))
from datetime import datetime
import os
import json

app = Flask(__name__)
app.secret_key = 'restaurant_secret_key_2026'

# Force UTF-8 for all responses
@app.after_request
def add_charset(response):
    if response.content_type.startswith('text/html'):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

# ─── DATABASE CONFIG ──────────────────────────────────────────────
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3307))
DB_NAME = os.getenv('DB_NAME', 'restaurant')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '123456')

def get_db():
    if USE_PYMYSQL:
        try:
            conn = pymysql.connect(
                host=DB_HOST, port=DB_PORT,
                db=DB_NAME, user=DB_USER, password=DB_PASSWORD,
                charset='utf8mb4',
                use_unicode=True,
                cursorclass=pymysql.cursors.DictCursor,
                init_command="SET time_zone = '+07:00'",
                connect_timeout=10,
            )
            return conn
        except Exception as e:
            print(f"[PyMySQL ERROR] {e}")
            return None
    else:
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=DB_HOST, port=DB_PORT,
                database=DB_NAME, user=DB_USER, password=DB_PASSWORD,
                charset='utf8mb4', use_unicode=True,
                connection_timeout=10,
            )
            cur = conn.cursor()
            cur.execute("SET time_zone = '+07:00'")
            cur.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.close()
            return conn
        except Exception as e:
            print(f"[MySQL Connector ERROR] {e}")
            return None

def query(sql, params=None, fetchone=False, commit=False):
    """Safe query - returns {} or [] instead of None on error"""
    conn = get_db()
    if not conn:
        print("[QUERY] No DB connection")
        return {} if fetchone else []
    try:
        if USE_PYMYSQL:
            cur = conn.cursor(pymysql.cursors.DictCursor)
        else:
            cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        if commit:
            conn.commit()
            return cur.lastrowid or 0
        if fetchone:
            result = cur.fetchone()
            return result if result is not None else {}
        results = cur.fetchall()
        print(f"[QUERY OK] rows={len(results)} sql={sql[:60]}")
        return results or []
    except Exception as e:
        print(f"[QUERY ERROR] {e} | sql={sql[:80]}")
        return {} if fetchone else []
    finally:
        try:
            conn.close()
        except:
            pass

# ─── AUTH HELPERS ─────────────────────────────────────────────────
def login_required(roles=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'staff_id' not in session:
                return redirect(url_for('login'))
            if roles and session.get('role') not in roles:
                flash('Bạn không có quyền truy cập trang này.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

def format_currency(amount):
    return f"{int(amount):,}đ"


# ─── CATEGORY EMOJI MAP ───────────────────────────────────────────
CATEGORY_EMOJI = {
    'khai-vi':     '🥗',
    'mon-chinh':   '🍖',
    'com-mi':      '🍜',
    'lau-nuong':   '🔥',
    'trang-mieng': '🍮',
    'do-uong':     '🥤',
}

def get_cat_emoji(icon_code):
    return CATEGORY_EMOJI.get(icon_code, '🍽️')

app.jinja_env.filters['currency'] = format_currency
app.jinja_env.globals['get_cat_emoji'] = get_cat_emoji



# ─── DB HEALTH CHECK ─────────────────────────────────────────────
@app.route('/db-check')
def db_check():
    """Kiểm tra kết nối DB - truy cập http://localhost:5000/db-check"""
    conn = get_db()
    if not conn:
        return '''<h2 style="color:red">❌ Không kết nối được MySQL!</h2>
        <p>Kiểm tra:</p>
        <ol>
        <li>XAMPP → MySQL đang <b>Running</b> chưa?</li>
        <li>Database <b>restaurant_db</b> đã import <b>database.sql</b> chưa?</li>
        <li>Mở <a href="http://localhost/phpmyadmin">phpMyAdmin</a> kiểm tra</li>
        </ol>''', 500
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM staff")
        count = list(cur.fetchone().values())[0]
        conn.close()
        return f'<h2 style="color:green">✅ Kết nối MySQL thành công!</h2><p>Bảng staff có {count} tài khoản.</p><p><a href="/">Về trang chính</a></p>'
    except Exception as e:
        return f'<h2 style="color:orange">⚠️ Kết nối được MySQL nhưng thiếu database!</h2><p>Lỗi: {e}</p><p>Hãy import file <b>database.sql</b> vào phpMyAdmin</p>', 500

# ─── AUTH ROUTES ──────────────────────────────────────────────────
@app.route('/')
def index():
    if 'staff_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        staff = query(
            "SELECT * FROM staff WHERE username = %s AND is_active = 1",
            (username,), fetchone=True
        )
        
        if staff and isinstance(staff, dict) and staff.get('password_hash') and check_password_hash(staff['password_hash'], request.form.get('password', '')):
            session['staff_id'] = staff['id']
            session['staff_name'] = staff['full_name']
            session['role'] = staff['role']
            
            # Role-based redirect
            if staff['role'] == 'kitchen':
                return redirect(url_for('kitchen'))
            return redirect(url_for('dashboard'))
        
        flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── DASHBOARD ────────────────────────────────────────────────────
def safe_get(d, key, default=0):
    """Safely get value from query result dict"""
    if not d or not isinstance(d, dict):
        return default
    return d.get(key, default) or default

@app.route('/dashboard')
@login_required()
def dashboard():
    # Stats - dùng safe_get để tránh crash khi DB lỗi
    stats = {
        'pending':       safe_get(query("SELECT COUNT(*) as c FROM orders WHERE status='pending'", fetchone=True), 'c'),
        'cooking':       safe_get(query("SELECT COUNT(*) as c FROM orders WHERE status='cooking'", fetchone=True), 'c'),
        'ready':         safe_get(query("SELECT COUNT(*) as c FROM orders WHERE status='ready'",   fetchone=True), 'c'),
        'today_revenue': safe_get(query("SELECT COALESCE(SUM(total_amount),0) as r FROM orders WHERE status='paid' AND DATE(paid_at)=CURDATE()", fetchone=True), 'r'),
        'today_orders':  safe_get(query("SELECT COUNT(*) as c FROM orders WHERE DATE(created_at)=CURDATE()", fetchone=True), 'c'),
    }
    
    active_orders = query("""
        SELECT o.*, t.table_number, s.full_name as staff_name,
               COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        LEFT JOIN staff s ON o.staff_id = s.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.status IN ('pending','cooking','ready')
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """)
    
    tables = query("SELECT * FROM tables ORDER BY table_number")
    
    return render_template('dashboard.html', stats=stats, active_orders=active_orders, tables=tables)

# ─── MENU (Customer View) ─────────────────────────────────────────
@app.route('/menu')
def menu():
    categories = query("SELECT * FROM categories ORDER BY display_order")
    items = query("""
        SELECT mi.*, c.name as category_name 
        FROM menu_items mi
        JOIN categories c ON mi.category_id = c.id
        WHERE mi.is_available = 1
        ORDER BY c.display_order, mi.display_order
    """)
    
    # Group items by category
    menu_data = {}
    for cat in categories:
        menu_data[cat['id']] = {
            'category': cat,
            'items': [i for i in items if i['category_id'] == cat['id']]
        }
    
    return render_template('menu.html', menu_data=menu_data, categories=categories)

# ─── ORDER MANAGEMENT ────────────────────────────────────────────
@app.route('/orders')
@login_required(roles=['admin', 'waiter'])
def orders():
    status_filter = request.args.get('status', 'all')
    table_filter = request.args.get('table', 'all')
    
    sql = """
        SELECT o.*, t.table_number, s.full_name as staff_name,
               COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        LEFT JOIN staff s ON o.staff_id = s.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE 1=1
    """
    params = []
    
    if status_filter != 'all':
        sql += " AND o.status = %s"
        params.append(status_filter)
    
    if table_filter != 'all':
        sql += " AND o.table_id = %s"
        params.append(table_filter)
    
    sql += " GROUP BY o.id ORDER BY o.created_at DESC LIMIT 100"
    
    orders_list = query(sql, tuple(params) if params else None)
    tables = query("SELECT * FROM tables ORDER BY table_number")
    
    return render_template('orders.html', orders=orders_list, tables=tables,
                           status_filter=status_filter, table_filter=table_filter)

@app.route('/orders/new', methods=['GET', 'POST'])
@login_required(roles=['admin', 'waiter'])
def new_order():
    if request.method == 'POST':
        data = request.json
        table_id = data.get('table_id')
        items = data.get('items', [])
        notes = data.get('notes', '')
        
        if not items:
            return jsonify({'success': False, 'message': 'Chưa có món nào!'})
        
        # Calculate total
        total = sum(item['price'] * item['quantity'] for item in items)
        
        # Create order
        order_id = query(
            "INSERT INTO orders (table_id, staff_id, notes, total_amount) VALUES (%s, %s, %s, %s)",
            (table_id, session['staff_id'], notes, total), commit=True
        )
        
        # Insert order items
        for item in items:
            mid      = int(item['menu_item_id'])
            qty      = int(item['quantity'])
            price    = float(item['price'])
            subtotal = item['price'] * item['quantity']
            query(
                "INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, subtotal, notes) VALUES (%s,%s,%s,%s,%s,%s)",
                (order_id, item['menu_item_id'], item['quantity'], item['price'], subtotal, item.get('notes','')),
                commit=True
            )
        
        # Update table status
        if table_id:
            query("UPDATE tables SET status='occupied' WHERE id=%s", (table_id,), commit=True)
        
        return jsonify({'success': True, 'order_id': order_id, 'message': f'Đã tạo đơn #{order_id}'})
    
    # GET
    categories = query("SELECT * FROM categories ORDER BY display_order")
    items = query("""
        SELECT mi.*, c.name as category_name 
        FROM menu_items mi JOIN categories c ON mi.category_id = c.id
        WHERE mi.is_available = 1
        ORDER BY c.display_order, mi.display_order
    """)
    tables = query("SELECT * FROM tables WHERE status != 'occupied' ORDER BY table_number")
    all_tables = query("SELECT * FROM tables ORDER BY table_number")
    
    menu_by_cat = {}
    for cat in categories:
        menu_by_cat[cat['id']] = {
            'category': cat,
            'items': [i for i in items if i['category_id'] == cat['id']]
        }
    
    return render_template('new_order.html', menu_by_cat=menu_by_cat,
                           categories=categories, tables=tables, all_tables=all_tables)

@app.route('/orders/<int:order_id>')
@login_required()
def order_detail(order_id):
    order = query("SELECT o.*, t.table_number, s.full_name as staff_name FROM orders o LEFT JOIN tables t ON o.table_id=t.id LEFT JOIN staff s ON o.staff_id=s.id WHERE o.id=%s", (order_id,), fetchone=True)
    if not order:
        flash('Không tìm thấy đơn hàng!', 'error')
        return redirect(url_for('orders'))
    
    items = query("""
        SELECT oi.*, mi.name as item_name FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = %s
    """, (order_id,))
    
    return render_template('order_detail.html', order=order, items=items)

@app.route('/orders/<int:order_id>/send-kitchen', methods=['POST'])
@login_required(roles=['admin', 'waiter'])
def send_to_kitchen(order_id):
    query("UPDATE orders SET status='cooking', updated_at=NOW() WHERE id=%s", (order_id,), commit=True)
    return jsonify({'success': True, 'message': 'Đã gửi bếp!'})

@app.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required()
def update_status(order_id):
    new_status = request.json.get('status')
    valid = ['pending', 'cooking', 'ready', 'cancelled']
    if new_status not in valid:
        return jsonify({'success': False, 'message': 'Trạng thái không hợp lệ'})
    
    query("UPDATE orders SET status=%s, updated_at=NOW() WHERE id=%s", (new_status, order_id), commit=True)
    return jsonify({'success': True})

@app.route('/orders/<int:order_id>/pay', methods=['POST'])
@login_required(roles=['admin', 'waiter'])
def pay_order(order_id):
    payment_method = request.json.get('payment_method', 'cash')
    
    order = query("SELECT * FROM orders WHERE id=%s", (order_id,), fetchone=True)
    if not order:
        return jsonify({'success': False, 'message': 'Không tìm thấy đơn'})
    
    query(
        "UPDATE orders SET status='paid', payment_method=%s, paid_at=NOW() WHERE id=%s",
        (payment_method, order_id), commit=True
    )
    
    # Free the table
    if order['table_id']:
        query("UPDATE tables SET status='available' WHERE id=%s", (order['table_id'],), commit=True)
    
    return jsonify({'success': True, 'message': 'Thanh toán thành công!'})

# ─── KITCHEN VIEW ─────────────────────────────────────────────────
@app.route('/kitchen')
@login_required(roles=['admin', 'kitchen'])
def kitchen():
    return render_template('kitchen.html')

@app.route('/api/kitchen/orders')
@login_required(roles=['admin', 'kitchen'])
def kitchen_orders():
    orders_list = query("""
        SELECT o.id, o.status, o.notes, o.created_at, o.updated_at,
               t.table_number
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        WHERE o.status IN ('cooking', 'pending')
        ORDER BY o.created_at ASC
    """)
    
    for order in orders_list:
        order['items'] = query("""
            SELECT oi.quantity, oi.notes, mi.name
            FROM order_items oi JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE oi.order_id = %s
        """, (order['id'],))
        order['created_at'] = order['created_at'].isoformat() if order['created_at'] else None
        order['updated_at'] = order['updated_at'].isoformat() if order['updated_at'] else None
    
    return jsonify(orders_list)

@app.route('/api/kitchen/ready/<int:order_id>', methods=['POST'])
@login_required(roles=['admin', 'kitchen'])
def mark_ready(order_id):
    query("UPDATE orders SET status='ready', updated_at=NOW() WHERE id=%s", (order_id,), commit=True)
    return jsonify({'success': True})

# ─── ADMIN PANEL ──────────────────────────────────────────────────
@app.route('/admin')
@login_required(roles=['admin'])
def admin():
    return redirect(url_for('admin_menu'))

@app.route('/admin/menu')
@login_required(roles=['admin'])
def admin_menu():
    categories = query("SELECT * FROM categories ORDER BY display_order")
    items = query("""
        SELECT mi.*, c.name as cat_name FROM menu_items mi
        JOIN categories c ON mi.category_id = c.id
        ORDER BY c.display_order, mi.display_order
    """)
    return render_template('admin_menu.html', categories=categories, items=items)

@app.route('/admin/menu/toggle/<int:item_id>', methods=['POST'])
@login_required(roles=['admin'])
def toggle_item(item_id):
    query("UPDATE menu_items SET is_available = NOT is_available WHERE id=%s", (item_id,), commit=True)
    return jsonify({'success': True})

@app.route('/admin/menu/item', methods=['POST'])
@login_required(roles=['admin'])
def save_item():
    data = request.json
    item_id = data.get('id')
    
    if item_id:
        query("""UPDATE menu_items SET name=%s, description=%s, price=%s, category_id=%s WHERE id=%s""",
              (data['name'], data.get('description',''), data['price'], data['category_id'], item_id), commit=True)
    else:
        query("""INSERT INTO menu_items (name, description, price, category_id, is_available) VALUES (%s,%s,%s,%s,1)""",
              (data['name'], data.get('description',''), data['price'], data['category_id']), commit=True)
    
    return jsonify({'success': True})

@app.route('/admin/menu/item/<int:item_id>', methods=['DELETE'])
@login_required(roles=['admin'])
def delete_item(item_id):
    query("DELETE FROM menu_items WHERE id=%s", (item_id,), commit=True)
    return jsonify({'success': True})

@app.route('/admin/staff')
@login_required(roles=['admin'])
def admin_staff():
    staff_list = query("SELECT id, username, full_name, role, is_active, created_at FROM staff ORDER BY role, full_name")
    return render_template('admin_staff.html', staff_list=staff_list)

@app.route('/admin/staff/save', methods=['POST'])
@login_required(roles=['admin'])
def save_staff():
    data = request.json or {}
    staff_id = data.get('id')

    # Validate cơ bản
    if not data.get('full_name') or not data.get('role'):
        return jsonify({'success': False, 'message': 'Thiếu thông tin'}), 400

    if staff_id:
        # UPDATE
        if data.get('password'):
            pw_hash = generate_password_hash(data['password'])
            query("""
                UPDATE staff 
                SET full_name=%s, role=%s, password_hash=%s 
                WHERE id=%s
            """, (data['full_name'], data['role'], pw_hash, staff_id), commit=True)
        else:
            query("""
                UPDATE staff 
                SET full_name=%s, role=%s 
                WHERE id=%s
            """, (data['full_name'], data['role'], staff_id), commit=True)
    else:
        # CREATE
        if not data.get('username') or not data.get('password'):
            return jsonify({'success': False, 'message': 'Thiếu username/password'}), 400

        pw_hash = generate_password_hash(data['password'])

        query("""
            INSERT INTO staff (username, password_hash, full_name, role) 
            VALUES (%s,%s,%s,%s)
        """, (data['username'], pw_hash, data['full_name'], data['role']), commit=True)

    return jsonify({'success': True})

@app.route('/admin/staff/toggle/<int:staff_id>', methods=['POST'])
@login_required(roles=['admin'])
def toggle_staff(staff_id):
    query("UPDATE staff SET is_active = NOT is_active WHERE id=%s", (staff_id,), commit=True)
    return jsonify({'success': True})

@app.route('/admin/reports')
@login_required(roles=['admin'])
def admin_reports():
    # Revenue last 7 days
    daily_revenue = query("""
        SELECT DATE(paid_at) as date, 
               COUNT(*) as order_count,
               SUM(total_amount) as revenue
        FROM orders WHERE status='paid' AND paid_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(paid_at) ORDER BY date ASC
    """)
    
    # Top items
    top_items = query("""
        SELECT mi.name, SUM(oi.quantity) as qty, SUM(oi.subtotal) as revenue
        FROM order_items oi JOIN menu_items mi ON oi.menu_item_id = mi.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status='paid' AND DATE(o.paid_at) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY mi.id ORDER BY qty DESC LIMIT 10
    """)
    
    # Today stats
    today = query("""
        SELECT COUNT(*) as orders,
               COALESCE(SUM(total_amount),0) as revenue,
               COALESCE(AVG(total_amount),0) as avg_order
        FROM orders WHERE status='paid' AND DATE(paid_at)=CURDATE()
    """, fetchone=True)
    
    # Payment method breakdown
    payment_stats = query("""
        SELECT payment_method, COUNT(*) as count, SUM(total_amount) as total
        FROM orders WHERE status='paid' AND DATE(paid_at) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY payment_method
    """)
    
    return render_template('admin_reports.html',
                           daily_revenue=daily_revenue, top_items=top_items,
                           today=today, payment_stats=payment_stats)

# ─── API ENDPOINTS ────────────────────────────────────────────────
@app.route('/api/orders/active')
@login_required()
def api_active_orders():
    orders_list = query("""
        SELECT o.id, o.status, o.total_amount, o.created_at,
               t.table_number, COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.status IN ('pending','cooking','ready')
        GROUP BY o.id ORDER BY o.created_at DESC
    """)
    for o in orders_list:
        o['created_at'] = o['created_at'].isoformat()
        o['total_amount'] = float(o['total_amount'])
    return jsonify(orders_list)

@app.route('/api/tables')
@login_required()
def api_tables():
    tables = query("SELECT * FROM tables ORDER BY table_number")
    return jsonify(tables)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)