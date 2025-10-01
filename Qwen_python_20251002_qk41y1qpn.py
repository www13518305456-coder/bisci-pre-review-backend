from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app) # 允许跨域请求

# --- 配置 ---
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 20 * 1024 * 1024 # 限制上传文件大小为 20MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- 模拟数据存储 ---
# 在实际应用中，这里应该是数据库操作 (如 SQLAlchemy + SQLite/PostgreSQL/MySQL)
verification_codes = {} # 存储手机号和验证码及过期时间的字典
pre_review_submissions = {} # 存储预审提交信息的字典

# --- API 路由 ---

@app.route('/api/send-verification-code', methods=['POST'])
def send_verification_code():
    data = request.get_json()
    phone = data.get('phone')

    if not phone or len(phone) != 11 or not phone.isdigit():
        return jsonify({'success': False, 'message': '无效的手机号码'}), 400

    # 生成6位随机验证码
    code = f"{random.randint(100000, 999999)}"
    print(f"[模拟] 发送验证码 {code} 到手机号: {phone}") # 实际应用中应调用短信服务API

    # 存储验证码和过期时间 (模拟)
    expiration_time = datetime.now() + timedelta(minutes=5)
    verification_codes[phone] = {'code': code, 'expires_at': expiration_time}

    # 模拟发送成功
    return jsonify({'success': True, 'message': '验证码已发送'})


@app.route('/api/submit-pre-review', methods=['POST'])
def submit_pre_review():
    try:
        # --- 获取表单数据 ---
        journal_type = request.form.get('journalType')
        paper_title = request.form.get('paperTitle')
        research_field = request.form.get('researchField')
        research_direction = request.form.get('researchDirection')
        paper_type = request.form.get('paperType')
        submission_count = request.form.get('submissionCount')
        author_name = request.form.get('authorName')
        wechat_name = request.form.get('wechatName')
        education = request.form.get('education')
        phone = request.form.get('phone')
        verify_code = request.form.get('verifyCode')
        identity = request.form.get('identity')
        title = request.form.get('title')
        purpose = request.form.get('purpose')

        # --- 获取上传文件 ---
        paper_file = request.files.get('paperFile')

        # --- 验证输入 ---
        if not all([journal_type, paper_title, research_field, research_direction, paper_type, submission_count,
                    author_name, wechat_name, education, phone, verify_code, identity, title, purpose]):
            return jsonify({'success': False, 'message': '请填写所有必填项'}), 400

        if not paper_file or paper_file.filename == '':
            return jsonify({'success': False, 'message': '请上传论文文件'}), 400

        # 验证验证码
        stored_data = verification_codes.get(phone)
        if not stored_data or stored_data['code'] != verify_code or datetime.now() > stored_data['expires_at']:
            return jsonify({'success': False, 'message': '验证码错误或已过期'}), 400

        # --- 处理文件 ---
        # 生成唯一文件名
        filename = str(uuid.uuid4()) + os.path.splitext(paper_file.filename)[1]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        paper_file.save(file_path) # 保存文件到本地

        # --- 生成预审编号 ---
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = f"{random.randint(1000, 9999)}"
        pre_review_code = f"PR-{timestamp}-{random_part}"

        # --- 存储提交信息 (模拟) ---
        submission_data = {
            'pre_review_code': pre_review_code,
            'journal_type': journal_type.split(','), # 将字符串转回列表
            'paper_title': paper_title,
            'research_field': research_field,
            'research_direction': research_direction,
            'paper_type': paper_type,
            'submission_count': submission_count,
            'author_name': author_name,
            'wechat_name': wechat_name,
            'education': education,
            'phone': phone,
            'verify_code': verify_code, # 实际应用中不应存储或立即清除
            'identity': identity,
            'title': title,
            'purpose': purpose,
            'file_path': file_path, # 存储文件路径
            'status': 'pending', # 预审状态: pending, reviewing, approved, rejected
            'submitted_at': datetime.now()
        }

        pre_review_submissions[pre_review_code] = submission_data

        # 验证码使用后清除
        del verification_codes[phone]

        print(f"[模拟] 收到预审提交: {pre_review_code}", submission_data)

        return jsonify({
            'success': True,
            'message': '论文提交成功',
            'preReviewCode': pre_review_code
        })

    except Exception as e:
        print(f"提交预审时发生错误: {e}")
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500


@app.route('/api/check-review-status/<code>', methods=['GET'])
def check_review_status(code):
    submission = pre_review_submissions.get(code)

    if not submission:
        return jsonify({'success': False, 'message': '未找到该预审编号的记录'}), 404

    # 模拟状态变化 (例如，提交后24小时内为pending，之后随机批准或拒绝)
    time_diff = (datetime.now() - submission['submitted_at']).total_seconds() / (60 * 60) # 小时差
    if time_diff > 24: # 模拟处理时间
        if submission['status'] == 'pending':
            submission['status'] = 'approved' if random.random() > 0.3 else 'rejected' # 70% 概率批准

    return jsonify({
        'success': True,
        'data': {
            'preReviewCode': submission['pre_review_code'],
            'status': submission['status'],
            'paperTitle': submission['paper_title'],
            'submittedAt': submission['submitted_at'].isoformat(), # 转换为 ISO 格式字符串
            # 可以添加更多状态详情
        }
    })


# --- 运行应用 ---
if __name__ == '__main__':
    # Render 会设置 PORT 环境变量
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False) # 生产环境应关闭 debug