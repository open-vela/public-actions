#!/bin/bash

# CLA API 测试脚本
# 用于测试 CLA 接口的连通性和响应

set -e

CLA_API_URL="https://vela-website.hybrid.xiaomi.com/openvela_cla/check"

echo "🧪 Testing CLA API..."
echo "API URL: $CLA_API_URL"
echo ""

# 测试用例
test_emails=(
    "liujinye@xiaomi.com"
    "test@example.com"
    "nonexistent@test.com"
)

for email in "${test_emails[@]}"; do
    echo "📧 Testing email: $email"
    
    # 发送请求并获取 HTTP 状态码
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/cla_test_response.txt \
        "$CLA_API_URL?email=$email")
    
    RESPONSE=$(cat /tmp/cla_test_response.txt)
    
    echo "   HTTP Code: $HTTP_CODE"
    echo "   Response: $RESPONSE"
    
    if [ "$HTTP_CODE" = "200" ]; then
        if [ "$RESPONSE" = "EMAIL_SIGNED" ]; then
            echo "   ✅ CLA signed"
        else
            echo "   ❌ CLA not signed"
        fi
    else
        echo "   ⚠️  API error"
    fi
    
    echo ""
done

echo "🏁 Test completed"

# 清理临时文件
rm -f /tmp/cla_test_response.txt