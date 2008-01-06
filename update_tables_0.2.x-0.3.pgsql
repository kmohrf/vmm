-- $Id$

DROP VIEW ma_aliases_count;
CREATE OR REPLACE VIEW vmm_alias_count AS
    SELECT count(DISTINCT address) AS aliases, gid
      FROM alias
  GROUP BY gid;

