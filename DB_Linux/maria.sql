CREATE DATABASE PVS;

USE PVS;


-- 센서를 받아서 저장할 위치
CREATE TABLE sensor_logs (
    id BIGINT NOT NULL AUTO_INCREMENT,
    sensor_time DATETIME(3) NOT NULL,
    speed FLOAT NULL,
    acc_x FLOAT NULL,
    acc_y FLOAT NULL,
    acc_z FLOAT NULL,
    realtime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_sensor_time (sensor_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 최근 저장한 시뮬레이션 센서 시간을 저장
-- 실행 중단 시 자동 재개할 때 필요
CREATE TABLE process_state (
    id INT NOT NULL,
    last_sensor_time DATETIME NULL,
    updated_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- process_state는 한 줄 씩만 저장됨. 기본 한 줄 넣어두기
INSERT INTO process_state (id, last_sensor_time)
VALUES (1, NULL)
ON DUPLICATE KEY UPDATE id=id;


--table 확인하기
SHOW tables;
DESCRIBE sensor_logs;
DESCRIBE process_state;

SELECT * FROM sensor_logs;
SELECT * FROM process_state;