-- ---
-- Use this file to update the database layout, if you are upgrading your
-- Dovecot < v1.2.beta2 to Dovecot >= v1.2.beta2.
-- 
-- IMPORTANT
-- This file supports only the current vmm 0.6.0 database layout.
-- ---

SET client_encoding = 'UTF8';
SET client_min_messages = warning;


ALTER TABLE service_set DROP CONSTRAINT ukey_service_set;
ALTER TABLE service_set RENAME managesieve to sieve;
ALTER TABLE service_set
    ADD CONSTRAINT ukey_service_set UNIQUE (smtp, pop3, imap, sieve);


DROP TRIGGER mergeuserquota_11 ON userquota_11;
DROP FUNCTION merge_userquota_11();
DROP TABLE userquota_11;


DROP TYPE dovecotpassword CASCADE;
CREATE TYPE dovecotpassword AS (
    userid    varchar(320),
    password  varchar(270),
    smtp      boolean,
    pop3      boolean,
    imap      boolean,
    sieve     boolean
);

CREATE OR REPLACE FUNCTION dovecotpassword(
    IN localpart varchar, IN the_domain varchar) RETURNS SETOF dovecotpassword
AS $$
    DECLARE
        record dovecotpassword;
        userid varchar(320) := localpart || '@' || the_domain;
    BEGIN
        FOR record IN
            SELECT userid, passwd, smtp, pop3, imap, sieve
              FROM users, service_set, domain_data
             WHERE users.gid = (SELECT gid
                                  FROM domain_name
                                 WHERE domainname = the_domain)
               AND local_part = localpart
               AND users.gid = domain_data.gid
               AND CASE WHEN
                     users.ssid IS NOT NULL
                     THEN
                       service_set.ssid = users.ssid
                     ELSE
                       service_set.ssid = domain_data.ssid
                     END
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;


CREATE TABLE userquota (
    uid         bigint NOT NULL,
    bytes       bigint NOT NULL DEFAULT 0,
    messages    integer NOT NULL DEFAULT 0,
    CONSTRAINT  pkey_userquota PRIMARY KEY (uid),
    CONSTRAINT  fkey_userquota_uid_users FOREIGN KEY (uid)
        REFERENCES users (uid) ON DELETE CASCADE
);

CREATE OR REPLACE FUNCTION merge_userquota() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.messages < 0 OR NEW.messages IS NULL THEN
        IF NEW.messages IS NULL THEN
            NEW.messages = 0;
        ELSE
            NEW.messages = -NEW.messages;
        END IF;
        RETURN NEW;
    END IF;
    LOOP
        UPDATE userquota
           SET bytes = bytes + NEW.bytes, messages = messages + NEW.messages
         WHERE uid = NEW.uid;
        IF found THEN
            RETURN NULL;
        END IF;
        BEGIN
            IF NEW.messages = 0 THEN
              INSERT INTO userquota VALUES (NEW.uid, NEW.bytes, NULL);
            ELSE
              INSERT INTO userquota VALUES (NEW.uid, NEW.bytes, -NEW.messages);
            END IF;
            RETURN NULL;
        EXCEPTION
            WHEN unique_violation THEN
                -- do nothing, and loop to try the UPDATE again
            WHEN foreign_key_violation THEN
                -- break the loop: a non matching uid means no such user
                RETURN NULL;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mergeuserquota BEFORE INSERT ON userquota
    FOR EACH ROW EXECUTE PROCEDURE merge_userquota();
