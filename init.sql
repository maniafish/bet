CREATE TABLE rounds (
    bet_timestamp int(11) NOT NULL DEFAULT '0' COMMENT '当前时间戳(到分钟为止)，格式: 201912051700',
    bet_single int(11) NOT NULL DEFAULT '0' COMMENT '单下注倍率',
    bet_double int(11) NOT NULL DEFAULT '0' COMMENT '双下注倍率',
    bet_big int(11) NOT NULL DEFAULT '0' COMMENT '大下注倍率',
    bet_small int(11) NOT NULL DEFAULT '0' COMMENT '小下注倍率',
    roundid int(11) NOT NULL DEFAULT '0' COMMENT '当前轮次',
    state int(11) NOT NULL DEFAULT '0' COMMENT '本条记录状态: 0, 正常; -1, 记录异常; 1, 修复后的记录',
    importtime datetime DEFAULT NULL COMMENT '当前记录时间',
    updatetime timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (bet_timestamp),
    KEY (importtime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='轮次信息表';
