-- $Id$

-- --- Information:
-- This file contains some data types and functions these should speed up some
-- operations. Read the comment on each data type/functions for more details.
-- ---

-- ---
-- Data type for function postfix_smtpd_sender_login_map(varchar, varchar)
-- ---
CREATE TYPE sender_login AS (
    sender  varchar(320),
    login   text
);

-- ---
-- Parameters (from _sender_ address (MAIL FROM) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: SASL _login_ names that own _sender_ addresses (MAIL FROM):
--      set of sender_login records.
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON domain_name, users, alias TO postfix;
--
-- For more details see postconf(5) section smtpd_sender_login_maps
-- ---
CREATE OR REPLACE FUNCTION postfix_smtpd_sender_login_map(
    IN localpart varchar, IN the_domain varchar) RETURNS SETOF sender_login
AS $$
    DECLARE
        rec sender_login;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
        sender varchar(320) := localpart || '@' || the_domain;
    BEGIN
        -- Get all addresses for 'localpart' in the primary and aliased domains
        FOR rec IN
            SELECT sender, local_part || '@' || domainname
              FROM domain_name, users
             WHERE domain_name.gid = did
               AND users.local_part = localpart
            LOOP
                RETURN NEXT rec;
            END LOOP;
        IF NOT FOUND THEN
            -- Loop over the alias addresses for localpart@the_domain
            FOR rec IN
                SELECT DISTINCT sender, destination
                  FROM alias
                       LEFT JOIN domain_name USING (gid)
                 WHERE alias.address = localpart
                LOOP
                    RETURN NEXT rec;
                END LOOP;
        END IF;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;

-- ########################################################################## --

-- ---
-- Data type for function postfix_virtual_mailbox(varchar, varchar)
-- ---
CREATE TYPE address_maildir AS (
    address varchar(320),
    maildir text
);

-- ---
-- Parameters (from recipients address (MAIL TO) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: address_maildir records
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON domain_data,domain_name,maillocation,users TO postfix;
--
-- For more details see postconf(5) section virtual_mailbox_maps
-- ---
CREATE OR REPLACE FUNCTION postfix_virtual_mailbox_map(
   IN localpart varchar, IN the_domain varchar) RETURNS SETOF address_maildir
AS $$
    DECLARE
        rec address_maildir;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
        address varchar(320) := localpart || '@' || the_domain;
    BEGIN
        FOR rec IN
            SELECT address, domaindir||'/'||users.uid||'/'||maillocation||'/'
              FROM domain_data, users, maillocation
             WHERE domain_data.gid = did
               AND users.gid = did
               AND users.local_part = localpart
               AND maillocation.mid = users.mid
            LOOP
                RETURN NEXT rec;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;

-- ########################################################################## --

-- ---
-- Data type for functions: postfix_relocated_map(varchar, varchar)
--                          postfix_virtual_alias_map(varchar, varchar)
--                          
-- ---
CREATE TYPE recipient_destination AS (
    recipient   varchar(320),
    destination text
);

-- ---
-- Parameters (from recipients address (MAIL TO) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: recipient_destination records
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON alias, domain_name TO postfix;
--
-- For more details see postconf(5) section virtual_alias_maps and virtual(5)
-- ---
CREATE OR REPLACE FUNCTION postfix_virtual_alias_map(
    IN localpart varchar, IN the_domain varchar)
    RETURNS SETOF recipient_destination
AS $$
    DECLARE
        record recipient_destination;
        recipient varchar(320) := localpart || '@' || the_domain;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
    BEGIN
        FOR record IN
            SELECT recipient, destination
              FROM alias
             WHERE gid = did
               AND address = localpart
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;

-- ########################################################################## --

-- ---
-- Parameters (from recipients address (MAIL TO) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: recipient_destination records
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON domain_name, relocated TO postfix;
--
-- For more details see postconf(5) section relocated_maps and relocated(5)
-- ---
CREATE OR REPLACE FUNCTION postfix_relocated_map(
    IN localpart varchar, IN the_domain varchar)
    RETURNS SETOF recipient_destination
AS $$
    DECLARE
        record recipient_destination;
        recipient varchar(320) := localpart || '@' || the_domain;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
    BEGIN
        FOR record IN
            SELECT recipient, destination
              FROM relocated
             WHERE gid = did
               AND address = localpart
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;

-- ########################################################################## --

-- ---
-- Data type for function postfix_transport_map(varchar, varchar)
-- ---
CREATE TYPE recipient_transport AS (
    recipient   varchar(320),
    transport   text
);

-- ---
-- Parameters (from recipients address (MAIL TO) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: recipient_transport records
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON users, transport, domain_name TO postfix;
--
-- For more details see postconf(5) section transport_maps and transport(5)
-- ---
CREATE OR REPLACE FUNCTION postfix_transport_map(
    IN localpart varchar, IN the_domain varchar)
    RETURNS SETOF recipient_transport
AS $$
    DECLARE
        record recipient_transport;
        recipient varchar(320) := localpart || '@' || the_domain;
    BEGIN
        FOR record IN
            SELECT recipient, transport
              FROM transport
             WHERE tid = (SELECT tid
                            FROM users
                           WHERE gid = (SELECT gid
                                          FROM domain_name
                                         WHERE domainname = the_domain)
               AND local_part = localpart)
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;
