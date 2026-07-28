# Environment Secrets Store

Environment Secrets Store, NovaVision workflow içinde kullanılacak environment variable isimlerini alır, bu değişkenlerin runtime ortamında mevcut olup olmadığını kontrol eder ve gerçek secret değerlerini workflow çıktısına yazmadan yalnızca referanslarını downstream component'lere aktarır.

## Kullanım

Örnek giriş:

```json
["DOCKER_NETWORK"]
```

Üretilen çıktı:

```json
["DOCKER_NETWORK"]
```

Gerçek değer NovaVision runtime ortamında kalır ve output ekranında gösterilmez.

## Akış

```text
Environment Secrets Store.secretReferences
    → Secret Output Viewer.secretReferences
```

## Geliştirme

```bash
python -m pytest -q
```

Paket, secret değerlerini kaynak koda veya workflow tanımına gömmeden güvenli biçimde kullanılabilir hâle getirmek için geliştirilmiştir.
