import base64

# Base64 encoded text
encoded_text = "U29tZSB0ZXh0IGluIGZpbGUgd2l0aCB0aGUgY29uZmlndXJlZCBkYXRhIHdpdGggYW5lbnkgZGVmaW5lZCBmb3IgcGFyYWxsZWwgZW5jb2Rpbmcgb24gc3ViamVjdCBvYmplY3RzIGluIGNvbnRleHQgdGV4dC4gVGhpcyBpcyBvbmUgY2hhbGxlbmdlIGRlY3J5cH..."

decoded_bytes = base64.b64decode(encoded_text)
decoded_text = decoded_bytes.decode(errors="ignore")

print(decoded_text)
