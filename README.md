# PVS_DevOps


#### Description: Passive vehicle sensor monitoring and DevOps automatic operating system

## 1. 소개

수동 차량 센서 데이터를 이용해 가상 시뮬레이션의 모니터링을 하고, 프로세스가 끊길 시 자동 재개하는 시스템을 갖춘 프로그램입니다. 

### 1.1. 데이터 출처
센서 데이터는 Kaggle의 [Passive Vehicular Sensor - EDA]를 받아왔습니다. Thank You!! (To Gautam R Menon)

https://www.kaggle.com/code/gautamrmenon/passive-vehicular-sensor-eda/input?select=PVS+9


### 1.2. 디자인
UI 디자인은 WonderShare의 디자인이 예뻐서 참고할 생각이고, 4분할 할 겁니다.
<img width="800" alt="image" src="https://github.com/user-attachments/assets/a28fb967-bb1c-4212-85f6-869c1b2ef182" />

- 1사분면: 센서 데이터의 흐름과 트래픽 관리
- 2사분면: 차량 블랙박스
- 3사분면: GPS 지도
- 4사분면: 이슈 체크하는 로그창


