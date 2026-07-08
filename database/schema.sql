CREATE DATABASE IF NOT EXISTS cloudscope
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE cloudscope;

CREATE TABLE IF NOT EXISTS host_detail (
  hostid VARCHAR(32) PRIMARY KEY,
  hostname VARCHAR(128) NOT NULL,
  owner VARCHAR(64) NOT NULL,
  model VARCHAR(64) NOT NULL,
  location1 VARCHAR(64) NOT NULL,
  location2 VARCHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mod_detail (
  `mod` VARCHAR(64) PRIMARY KEY,
  `type` VARCHAR(16) NOT NULL,
  description VARCHAR(255) NOT NULL,
  unit VARCHAR(32) NOT NULL DEFAULT '',
  tag VARCHAR(64) NOT NULL,
  KEY idx_mod_type (`type`),
  KEY idx_mod_tag (tag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tsar_detail (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  ts BIGINT NOT NULL,
  collect_time DATETIME NOT NULL,
  hostid VARCHAR(32) NOT NULL,
  `type` VARCHAR(16) NOT NULL,
  `mod` VARCHAR(64) NOT NULL,
  value DECIMAL(18,4) NOT NULL,
  tag VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tsar_host FOREIGN KEY (hostid) REFERENCES host_detail(hostid),
  CONSTRAINT fk_tsar_mod FOREIGN KEY (`mod`) REFERENCES mod_detail(`mod`),
  CONSTRAINT uq_tsar_point UNIQUE (ts, hostid, `type`, `mod`),
  KEY idx_tsar_host_time (hostid, collect_time),
  KEY idx_tsar_mod_time (`mod`, collect_time),
  KEY idx_tsar_type_tag_time (`type`, tag, collect_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
