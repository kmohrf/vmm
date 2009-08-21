-- ---
-- with Dovecot v1.2.x the service managesieve was renamed to sieve
-- ---
ALTER TABLE users RENAME managesieve TO sieve;

DROP VIEW dovecot_password;
CREATE OR REPLACE VIEW dovecot_password AS
    SELECT local_part || '@' || domain_name.domainname AS "user",
           passwd AS "password", smtp, pop3, imap, sieve
      FROM users
           LEFT JOIN domain_name USING (gid);

