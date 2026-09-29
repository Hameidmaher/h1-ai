# 🔐 سياسة الأمان

## الإبلاغ

security@example.com — لا تفتح issue علني.

## الممارسات

### كلمات السر
- Argon2id (m=65536, t=3, p=4)
- طول أدنى 8 أحرف
- Rate limited (10/min)

### JWT
- Access: 30 دقيقة
- Refresh: 7 أيام
- HS256 signature

### Database
- RLS على الجداول الحساسة
- Prepared statements
- Audit logging

### الشبكة
- UFW active
- fail2ban
- البورتات الإدارية localhost
- HTTPS إجباري

## Checklist الإنتاج

- [x] HTTPS
- [x] Firewall (UFW)
- [x] fail2ban
- [x] Backups يومية
- [x] Monitoring
- [x] Admin password قوي
- [x] Rate limits
- [x] CORS مقيّد
