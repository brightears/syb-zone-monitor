-- Create email_contacts table for manual email management
CREATE TABLE IF NOT EXISTS email_contacts (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(100) DEFAULT 'Manager',
    is_active BOOLEAN DEFAULT TRUE,
    source VARCHAR(50) DEFAULT 'manual', -- 'manual' or 'api'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, email)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_email_contacts_account_id ON email_contacts(account_id);
CREATE INDEX IF NOT EXISTS idx_email_contacts_email ON email_contacts(email);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_email_contacts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_email_contacts_updated_at_trigger
    BEFORE UPDATE ON email_contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_email_contacts_updated_at();