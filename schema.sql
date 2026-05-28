CREATE TABLE IF NOT EXISTS `count` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `keyword` VARCHAR(255) NOT NULL,
  `total` BIGINT NOT NULL,
  `create_time` BIGINT DEFAULT NULL,
  `update_time` BIGINT DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `keyword` (`keyword`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
