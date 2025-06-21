# Version History

## v2.0-stable (June 19, 2025)
**Status**: Current stable version ✅

### Features
- ✅ Enhanced dashboard monitoring 863 accounts
- ✅ PostgreSQL database for status tracking
- ✅ Email notifications (fully functional)
- ✅ WhatsApp integration (tested, awaiting business number)
- ✅ Optimized zone checking for performance
- ✅ Contact management from CSV import
- ✅ Account search and filtering
- ✅ Notification history tracking
- ✅ Rate limiting protection

### Known Issues
- WhatsApp currently using test number (hello_world template only)
- Requires BMAsia business number for custom messages

### Rollback Command
```bash
git checkout v2.0-stable
```

---

## v1.0-stable (June 2025)
**Status**: Previous stable version

### Features
- Basic zone monitoring
- Simple dashboard
- Email notifications
- Initial PostgreSQL integration

### Rollback Command
```bash
git checkout v1.0-stable
```

---

## Version Management

### Creating New Stable Version
```bash
# When ready to create new stable version
git tag -a v3.0-stable -m "Description of what's stable"
git push origin v3.0-stable
```

### Viewing All Versions
```bash
git tag -l | grep stable
```

### Switching Versions
```bash
# To specific version
git checkout v2.0-stable

# Back to latest
git checkout main
```