# `analysis_jobs` 欄位語意

這份文件描述目前 MVP 實作下，`analysis_jobs` 各欄位的語意、寫入責任與 `NULL` 規則。

目前流程是：

1. 前端向 API 取得 presigned URL。
2. 前端將影片直接上傳到 R2。
3. 前端呼叫 `POST /jobs`。
4. API 建立一筆 `analysis_jobs`，狀態為 `uploaded`。
5. API 將 `job_id` enqueue 到 Redis / RQ。
6. Worker 取得 job 後，更新為 `processing`，下載影片並執行 `ffprobe`。
7. Worker 產生 analysis 用 normalized video 暫存檔，並再次執行 `ffprobe`。
8. Worker 成功時更新為 `done`，失敗時更新為 `failed`。

## 狀態欄位

目前實際會寫入的狀態只有：

- `uploaded`
- `processing`
- `done`
- `failed`

`validating` 目前仍在 schema 型別與資料表約束中，但現行程式沒有寫入它。它比較像保留給未來「validation 拆成獨立階段」時使用。

## 欄位對照

| 欄位                     | 可為 `NULL` | 誰寫入                    | 何時有值                                                                                        | 備註                                                                                                                              |
| ------------------------ | ----------- | ------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `id`                     | 否          | API                       | `POST /jobs` 建立 job 時                                                                        | 業務上的 job id。                                                                                                                 |
| `status`                 | 否          | API / worker              | 建立時為 `uploaded`；worker 開始處理時改為 `processing`；完成時改為 `done`；失敗時改為 `failed` | 代表整體 job lifecycle。                                                                                                          |
| `original_filename`      | 否          | API                       | `POST /jobs` 建立 job 時                                                                        | 來自前端請求。                                                                                                                    |
| `content_type`           | 否          | API                       | `POST /jobs` 建立 job 時                                                                        | 目前允許 `video/mp4`、`video/quicktime`、`video/webm`。                                                                           |
| `input_object_key`       | 否          | API                       | `POST /jobs` 建立 job 時                                                                        | 指向 R2 上傳完成的原始影片。                                                                                                      |
| `output_object_key`      | 是          | 未使用                    | 尚未有值                                                                                        | 預留給未來處理後輸出檔。                                                                                                          |
| `video_duration_seconds` | 是          | worker                    | `ffprobe` 成功後                                                                                | `NULL` 表示尚未完成探測或探測失敗。                                                                                               |
| `video_width`            | 是          | worker                    | `ffprobe` 成功後                                                                                | `NULL` 表示尚未完成探測或探測失敗。                                                                                               |
| `video_height`           | 是          | worker                    | `ffprobe` 成功後                                                                                | `NULL` 表示尚未完成探測或探測失敗。                                                                                               |
| `analysis_result`        | 是          | worker                    | worker 成功完成後                                                                               | JSONB。第一版先保存 normalization metadata、原始影片 metadata、analysis video metadata；MediaPipe / gait summary 之後會放在這裡。 |
| `error_message`          | 是          | API / worker              | enqueue 失敗時，或 worker 處理失敗時                                                            | `NULL` 表示目前沒有失敗訊息。                                                                                                     |
| `processing_started_at`  | 是          | worker                    | worker 開始處理時                                                                               | `NULL` 表示尚未被 worker 接手。                                                                                                   |
| `completed_at`           | 是          | worker                    | worker 成功完成時                                                                               | `NULL` 表示尚未成功完成。                                                                                                         |
| `failed_at`              | 是          | API / worker              | enqueue 失敗時，或 worker 處理失敗時                                                            | `NULL` 表示尚未失敗。                                                                                                             |
| `created_at`             | 否          | DB default                | row 建立時                                                                                      | 目前語意接近「job row 被建立的時間」，不是「上傳完成時間」。                                                                      |
| `updated_at`             | 否          | DB default + API / worker | row 建立時先有值，後續每次更新狀態時刷新                                                        | 共通系統欄位。                                                                                                                    |

## 目前重要語意

### `created_at`

`created_at` 目前不是使用者開始上傳的時間，也不是 R2 實際收到檔案的時間。

它目前代表的是：

> API 成功建立 `analysis_jobs` 這筆 row 的時間

因為現在 upload 是前端直傳 R2，API 並不直接接手檔案流。

### `video_*` 欄位

`video_duration_seconds`、`video_width`、`video_height` 現在必須允許 `NULL`，因為：

- job 先由 API 建立
- `ffprobe` 已經移到 worker
- metadata 不會在 `POST /jobs` 當下就存在

所以這三個欄位的 `NULL` 不是錯誤，而是「尚未探測完成」。

目前這三個欄位代表原始上傳影片的基礎 metadata，方便 API 與前端快速顯示。更完整的 analysis pipeline metadata 會寫入 `analysis_result`。

### `analysis_result`

`analysis_result` 是 worker 寫入的 JSONB 欄位。

目前第一版內容包含：

- `normalization`
  - 是否啟用 normalize
  - analysis video 的 timing mode
  - target fps
  - max long edge
  - normalized video 是否有永久 R2 object key
- `original_video`
  - 原始上傳影片的 `ffprobe` metadata
- `analysis_video`
  - normalized analysis video 的 `ffprobe` metadata

第一版 normalized video 只存在 worker 暫存磁碟，處理完成後會刪除，因此 `stored_object_key` 目前預期為 `NULL`。

### `error_message`

`error_message` 目前有兩個來源：

- API 已建立 DB row，但 enqueue 失敗
- worker 執行過程失敗

目前 `NULL` 表示「沒有記錄到失敗訊息」，不保證系統從未失敗過，只代表這筆 job 目前沒有被標成失敗。

目前錯誤訊息格式採用：

- 一般英文句子使用大寫開頭。
- 如果訊息以欄位名稱開頭，保留欄位名稱原樣，例如 `file_size`、`input_object_key`。
- 不在句尾加句號。
- 如果訊息必須以專有名詞、環境變數、欄位值或指令名稱開頭，保留原本大小寫，例如 `DATABASE_URL`、`ffmpeg`。

## 後續整理方向

之後如果把 validation 正式拆成獨立階段，可以再重新評估是否需要這些欄位：

- `validated_at`
- `validation_error_message`
- `validation_status`

到那時候，`validating` 這個狀態也才會真正成為實際流程的一部分。
