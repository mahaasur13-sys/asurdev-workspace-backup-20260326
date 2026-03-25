"""
Security Fix #4: Encrypted Backups
Шифрование локального хранилища
"""
import os
import json
import gzip
import hashlib
import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    print("Installing cryptography...")
    import subprocess
    subprocess.run(["pip", "install", "cryptography"], check=True)
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class BackupMetadata:
    backup_id: str
    timestamp: str
    checksum: str
    size_bytes: int
    encrypted: bool = True


class EncryptedBackup:
    """Encrypted backup system for asurdev data"""
    
    def __init__(self, backup_dir: str = "/home/workspace/asurdevSentinel/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from env or generate new"""
        key_env = os.environ.get("asurdev_BACKUP_KEY")
        
        if key_env:
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"asurdev_backup_salt",
                iterations=100000,
            )
            return base64.urlsafe_b64encode(kdf.derive(key_env.encode()))
        
        # Generate new key
        key_path = self.backup_dir / ".key"
        
        if key_path.exists():
            return key_path.read_bytes()
        
        # Create and save new key
        key = Fernet.generate_key()
        key_path.write_bytes(key)
        os.chmod(key_path, 0o600)  # Read-only for owner
        print(f"⚠️  New backup key created: {key_path}")
        print(f"⚠️  Save this key securely! Without it, backups cannot be restored.")
        return key
    
    def backup(self, data: dict, name: str = "default") -> BackupMetadata:
        """Create encrypted backup"""
        import uuid
        
        # Serialize
        json_data = json.dumps(data, default=str)
        
        # Compress
        compressed = gzip.compress(json_data.encode())
        
        # Encrypt
        encrypted = self.fernet.encrypt(compressed)
        
        # Create metadata
        backup_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        checksum = hashlib.sha256(encrypted).hexdigest()
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            timestamp=timestamp,
            checksum=checksum,
            size_bytes=len(encrypted),
            encrypted=True
        )
        
        # Save encrypted backup
        backup_file = self.backup_dir / f"{name}_{backup_id}.enc"
        backup_file.write_bytes(encrypted)
        
        # Save metadata
        meta_file = self.backup_dir / f"{name}_{backup_id}.meta"
        meta_file.write_text(json.dumps(asdict(metadata)))
        
        return metadata
    
    def restore(self, backup_id: str, name: str = "default") -> Optional[dict]:
        """Restore from encrypted backup"""
        # Find backup file
        pattern = f"{name}_{backup_id}"
        
        for enc_file in self.backup_dir.glob(f"{pattern}.enc"):
            try:
                # Read encrypted data
                encrypted = enc_file.read_bytes()
                
                # Verify checksum
                checksum = hashlib.sha256(encrypted).hexdigest()
                meta_file = enc_file.with_suffix(".meta")
                
                if meta_file.exists():
                    meta_dict = json.loads(meta_file.read_text())
                    if meta_dict["checksum"] != checksum:
                        raise ValueError("Checksum mismatch - backup corrupted!")
                
                # Decrypt
                compressed = self.fernet.decrypt(encrypted)
                
                # Decompress
                json_data = gzip.decompress(compressed)
                
                # Parse
                return json.loads(json_data)
                
            except Exception as e:
                print(f"Restore failed: {e}")
                return None
        
        return None
    
    def list_backups(self, name: str = "default") -> list[BackupMetadata]:
        """List all backups"""
        backups = []
        
        for meta_file in self.backup_dir.glob(f"{name}_*.meta"):
            try:
                data = json.loads(meta_file.read_text())
                backups.append(BackupMetadata(**data))
            except Exception:
                pass
        
        return sorted(backups, key=lambda x: x.timestamp, reverse=True)
    
    def prune_old(self, keep_last: int = 10, name: str = "default"):
        """Delete old backups, keeping only last N"""
        backups = self.list_backups(name)
        
        for backup in backups[keep_last:]:
            for ext in [".enc", ".meta"]:
                file = self.backup_dir / f"{name}_{backup.backup_id}{ext}"
                if file.exists():
                    file.unlink()
                    print(f"Deleted old backup: {file.name}")


class BackupScheduler:
    """Automatic backup scheduler"""
    
    def __init__(self, backup: EncryptedBackup, data_sources: list):
        self.backup = backup
        self.data_sources = data_sources
    
    async def run_backup(self, name: str = "asurdev"):
        """Run backup of all data sources"""
        import asyncio
        
        print(f"Starting backup: {name}")
        
        # Collect data from all sources
        all_data = {}
        
        for source in self.data_sources:
            try:
                if hasattr(source, "export"):
                    data = await source.export()
                    all_data[source.name] = data
                elif hasattr(source, "__dict__"):
                    all_data[type(source).__name__] = source.__dict__
            except Exception as e:
                print(f"Backup source failed: {e}")
        
        # Create backup
        metadata = self.backup.backup(all_data, name)
        
        print(f"Backup complete: {metadata.backup_id}")
        print(f"Size: {metadata.size_bytes / 1024:.1f} KB")
        
        # Prune old
        self.backup.prune_old(keep_last=10, name=name)
        
        return metadata


# Test
if __name__ == "__main__":
    eb = EncryptedBackup()
    
    # Test backup
    test_data = {
        "agents": {"market": {"signal": "BULLISH"}},
        "config": {"version": "2.1"},
        "timestamp": datetime.now().isoformat()
    }
    
    meta = eb.backup(test_data, "test")
    print(f"Backup created: {meta.backup_id}")
    
    # Test restore
    restored = eb.restore(meta.backup_id, "test")
    print(f"Restored: {restored is not None}")
    
    # List
    backups = eb.list_backups("test")
    print(f"Backups: {len(backups)}")
    
    print("\n✓ Encrypted backup module ready")
