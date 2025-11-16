import os

def create_minimal_pdf(file_path, content):
    with open(file_path, "wb") as f:
        # PDF Header
        f.write(b"%PDF-1.7\n")
        f.write(b"%\xe2\xe3\xcf\xd3\n")

        # PDF Body
        # Object 1: Catalog
        f.write(b"1 0 obj\n")
        f.write(b"<< /Type /Catalog /Pages 2 0 R >>\n")
        f.write(b"endobj\n")

        # Object 2: Pages
        f.write(b"2 0 obj\n")
        f.write(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n")
        f.write(b"endobj\n")

        # Object 3: Page
        f.write(b"3 0 obj\n")
        f.write(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> \n")
        f.write(b"endobj\n")

        # Object 4: Content Stream
        content_bytes = content.encode('utf-8')
        stream = b"BT /F1 12 Tf 100 700 Td (" + content_bytes + b") Tj ET"
        f.write(b"4 0 obj\n")
        f.write(b"<< /Length %d >>\n" % len(stream))
        f.write(b"stream\n")
        f.write(stream)
        f.write(b"\nendstream\n")
        f.write(b"endobj\n")

        # Object 5: Font
        f.write(b"5 0 obj\n")
        f.write(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n")
        f.write(b"endobj\n")

        # Cross-reference table (xref)
        xref_start = f.tell()
        f.write(b"xref\n")
        f.write(b"0 6\n")
        f.write(b"0000000000 65535 f \n")
        f.write(b"0000000015 00000 n \n")
        f.write(b"0000000060 00000 n \n")
        f.write(b"0000000111 00000 n \n")
        f.write(b"0000000230 00000 n \n")
        f.write(b"0000000333 00000 n \n")

        # PDF Trailer
        f.write(b"trailer\n")
        f.write(b"<< /Size 6 /Root 1 0 R >>\n")
        f.write(b"startxref\n")
        f.write(b"%d\n" % xref_start)
        f.write(b"%%EOF\n")

if __name__ == "__main__":
    create_minimal_pdf("valid_cv.pdf", "This is a valid PDF for testing.")
