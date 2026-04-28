-- Chạy tự động lần đầu tiên PostgreSQL khởi động
-- File này giúp setup schema ngay từ đầu

CREATE TABLE IF NOT EXISTS urls (
    id          SERIAL PRIMARY KEY,
    short_code  VARCHAR(10) UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    click_count INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Index để tìm kiếm nhanh theo short_code
CREATE INDEX IF NOT EXISTS idx_short_code ON urls(short_code);

-- Thêm vài dữ liệu mẫu để test ngay
INSERT INTO urls (short_code, original_url) VALUES
    ('github',  'https://github.com'),
    ('google',  'https://google.com'),
    ('yt',      'https://youtube.com')
ON CONFLICT DO NOTHING;
