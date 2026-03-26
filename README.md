# 🏥 診所每日記錄 (Clinic Tracker)

## 用途
中醫診所每日記錄工具，包含病人數量、收入計算、請假記錄、月度統計。

## 部署
- **GitHub Pages:** https://jaterc01.github.io/clinic-tracker/
- **GitHub Repo:** https://github.com/jaterc01/clinic-tracker
- **部署方式:** 推送到 `main` branch，GitHub Pages 自動部署

## 薪資公式
- 每日收入 = 1600×診數 + 內科×110 + 針傷×55 + 小針刀×0.4 + (水藥+藥粉)×0.2 + 其他×0.2
- 預估薪水 = (自費均攤 + 1600) × 有效診數 + 55000（牌照費）
- 請假扣：早診扣3000、午/晚診扣3500

## 技術
- 單一 HTML 檔（HTML + CSS + JS）
- Firebase Realtime Database 雲端同步
- 密碼保護登入

## 維護紀錄
- 2026-03-26: 修復日期導航時區 bug（toISOString UTC offset 問題）
