// ── Question ─────────────────────────────────────────────────────────────

export type QuestionType =
  | "single_choice"
  | "multiple_choice"
  | "true_false"
  | "fill_blank"
  | "short_answer";

export type Difficulty = "easy" | "normal" | "hard";

export type Visibility = "private" | "public";

export type Source = "import" | "manual";

export interface Question {
  id: number;
  owner_id: number | null;
  course_id: number | null;
  visibility: Visibility;
  source: Source;
  created_at: string | null;
  subject: string;
  chapter: string;
  type: QuestionType;
  question: string;
  options: Record<string, string> | null;
  answer: string;
  analysis: string;
  difficulty: Difficulty;
  line_number?: number;
}

export interface QuestionCreate {
  subject?: string;
  chapter?: string;
  type: QuestionType;
  question: string;
  options?: Record<string, string> | null;
  answer: string;
  analysis?: string;
  difficulty?: Difficulty;
  course_id?: number | null;
}

export interface QuestionUpdate {
  course_id?: number;
  subject?: string;
  chapter?: string;
  type?: QuestionType;
  question?: string;
  options?: Record<string, string> | null;
  answer?: string;
  analysis?: string;
  difficulty?: Difficulty;
}

// ── Course / Question Bank ───────────────────────────────────────────────

export interface Course {
  id: number;
  owner_id: number;
  name: string;
  description: string;
  subject: string;
  visibility: Visibility;
  created_at: string | null;
  question_count: number;
  practice_count?: number;
  last_practiced_at?: string | null;
}

export interface CourseCreate {
  name: string;
  description?: string;
  subject?: string;
  visibility?: Visibility;
}

export interface CourseUpdate {
  name?: string;
  description?: string;
  subject?: string;
}

// ── Practice ─────────────────────────────────────────────────────────────

export interface SubmitRequest {
  question_id: number;
  user_answer: string;
}

export interface SubmitResponse {
  is_correct: boolean;
  correct_answer: string;
  analysis: string;
  wrongbook_recorded: boolean;
}

export interface PracticeStats {
  today_count: number;
  total_count: number;
  correct_count: number;
  wrong_count: number;
  accuracy_rate: number;
  recent_count_7d: number;
}

export interface PracticeRecord {
  id: number;
  question_id: number | null;
  course_id: number | null;
  question_type: string | null;
  question_text: string;
  is_correct: boolean;
  user_answer: string;
  correct_answer: string;
  answered_at: string | null;
}

export interface PracticeHistory {
  items: PracticeRecord[];
  total: number;
  page: number;
  page_size: number;
}

// ── Wrong Book ───────────────────────────────────────────────────────────

export interface WrongRecord {
  id: number;
  question_id: number;
  question: Question;
  wrong_count: number;
  last_wrong_answer: string;
}

// ── Review ───────────────────────────────────────────────────────────────

export interface TodayReview {
  due_count: number;
  wrong_count: number;
  weak_types: WeakType[];
  recommended_modes: string[];
}

export interface WeakType {
  question_type: string;
  total_attempts: number;
  wrong_attempts: number;
  error_rate: number;
}

export interface DailyActivity {
  date: string;
  count: number;
}

export interface TypeDistribution {
  question_type: string;
  total_count: number;
  correct_count: number;
  wrong_count: number;
  accuracy_rate: number;
}

export interface Streak {
  current_streak: number;
  longest_streak: number;
  last_practiced_date: string | null;
}

export interface TagAccuracy {
  tag_id: number;
  tag_name: string;
  total_count: number;
  correct_count: number;
  accuracy_rate: number;
}

export interface TodayRecommendation {
  weak_tags: Array<{
    tag_id: number;
    tag_name: string;
    total_count: number;
    correct_count: number;
    accuracy_rate: number;
  }>;
  weak_types: WeakType[];
  due_count: number;
  due_question_ids: number[];
  recommended_modes: string[];
}

export interface CourseAnalytics {
  course_id: number;
  course_name: string;
  question_count: number;
  practice_count: number;
  accuracy_rate: number;
}

export interface ScoreBucket {
  label: string;
  count: number;
}

export interface Bookmark {
  id: number;
  question_id: number;
  folder_name: string;
  note: string;
  created_at: string | null;
  question?: Question | null;
}

export interface BookmarkList {
  items: Bookmark[];
  total: number;
  folders: string[];
}

export interface DueReviewItem {
  id: number;
  review_level: number;
  next_review_at: string | null;
  last_reviewed_at: string | null;
  consecutive_correct: number;
  review_mode: string;
  question: Question | null;
}

// ── Import ───────────────────────────────────────────────────────────────

export interface ImportTiming {
  extract_ms: number;
  chunk_ms: number;
  ai_ms: number;
  total_ms: number;
  chunks: number;
  ai_chunks: number[];
}

export interface ImportPreviewResponse {
  questions: Question[];
  suggested_course_name: string;
  warnings: string[];
  total_parsed: number;
  total_valid: number;
  total_invalid: number;
  timing: ImportTiming | null;
}

export interface ConfirmImportRequest {
  questions: Question[];
  course_id?: number;
  course_name?: string;
}

export interface ConfirmImportResponse {
  imported_count: number;
  course_id: number | null;
  course_name: string;
}

export interface FileExtractResponse {
  text: string;
  filename: string;
  suggested_course_name: string;
  timing: ImportTiming | null;
}

// ── Auth ─────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  username: string;
  role: string;
  permissions?: string[];
}

export type RoleName = "student" | "teacher" | "admin";

export interface Exam {
  id: number;
  title: string;
  description: string;
  course_id: number;
  creator_id: number;
  time_limit: number;
  total_score: number;
  is_shuffle: boolean;
  is_blind: boolean;
  status: "draft" | "published" | string;
  question_count: number;
  created_at: string | null;
}

export interface ExamQuestion {
  id: number;
  question_id: number;
  question_type: QuestionType | string;
  question: string;
  options: Record<string, string> | null;
  score: number;
  order_index: number;
}

export interface ExamDetail extends Exam {
  questions: ExamQuestion[];
}

export interface ExamCreate {
  title: string;
  course_id: number;
  description?: string;
  time_limit?: number;
  total_score?: number;
  is_shuffle?: boolean;
  is_blind?: boolean;
  question_ids?: number[];
}

export interface ExamAttempt {
  id: number;
  exam_id: number;
  user_id: number;
  started_at: string | null;
  submitted_at: string | null;
  score: number | null;
}

export interface ExamSubmissionCreate {
  answers: Record<string, string>;
}

export interface ExamResult {
  exam_id: number;
  submission_id: number;
  score: number;
  total_score: number;
  correct_count: number;
  wrong_count: number;
  accuracy_rate: number;
  submitted_at: string | null;
}

export interface ExamLeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  score: number;
  total_score: number;
  submitted_at: string | null;
}

export interface ExamLeaderboard {
  exam_id: number;
  entries: ExamLeaderboardEntry[];
  total: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  invite_code: string;
}

export interface TokenResponse {
  access_token: string;
  token: string;
  token_type: string;
}

// ── Chat ─────────────────────────────────────────────────────────────────

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  history?: ChatMessage[];
}

export interface ChatResponse {
  reply: string;
}

// ── Generic paginated response ───────────────────────────────────────────

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface OptionItem {
  key: string;
  value: string;
}

export interface QuestionMeta {
  subjects: string[];
  chapters: string[];
}
