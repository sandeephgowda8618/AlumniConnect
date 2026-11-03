export type RoleCode = 'ADMINISTRATOR' | 'MENTOR' | 'STUDENT';

export interface User {
  user_id: number;
  email: string;
  display_name: string;
  role: RoleCode;
  token_type?: string;
  access_token?: string;
}

export interface Skill {
  skill_id: number;
  skill_name: string;
  category?: string;
}

export interface MentorshipDomain {
  domain_id: number;
  domain_name: string;
  description?: string;
}

export interface Department {
  department_id: number;
  department_code: string;
  department_name: string;
}

export interface Company {
  company_id: number;
  company_name: string;
  industry?: string;
}

export interface StudentProfile {
  user_id: number;
  display_name: string;
  email?: string;
  student_number: string;
  department_id: number;
  department_name?: string;
  programme?: string;
  batch_year?: number;
  expected_graduation_year?: number;
  career_goal?: string;
  bio?: string;
  skills: { skill_id: number; skill_name: string; proficiency_level?: string }[];
  domain_interests: { domain_id: number; domain_name: string; priority_order?: number }[];
}

export interface MentorProfile {
  user_id: number;
  display_name: string;
  email?: string;
  job_title: string;
  years_experience: number;
  max_active_mentees: number;
  accepting_requests: boolean;
  professional_summary?: string;
  company_id?: number;
  company_name?: string;
  industry?: string;
  department_id: number;
  department_name?: string;
  skills: { skill_id: number; skill_name: string; endorsement_count?: number }[];
  domain_expertises: { domain_id: number; domain_name: string; expertise_level: string; is_primary: boolean }[];
  active_mentees_count?: number;
  average_rating?: number;
  review_count?: number;
}

export interface RecommendedMentor {
  mentor_user_id: number;
  full_name: string;
  job_title: string;
  company_name?: string;
  industry?: string;
  years_experience: number;
  rank_position: number;
  overall_score: number;
  skill_score: number;
  domain_score: number;
  experience_score: number;
  career_score: number;
  quality_score: number;
  explanation_text: string;
  matched_skills: string[];
  matched_domains: string[];
  shared_alumni: boolean;
  average_rating?: number;
  review_count: number;
  accepting_requests: boolean;
}

export interface MentorshipRequest {
  request_id: number;
  student_user_id: number;
  student_name?: string;
  student_programme?: string;
  mentor_user_id: number;
  mentor_name?: string;
  mentor_job_title?: string;
  domain_id: number;
  domain_name?: string;
  request_message: string;
  career_goal_snapshot?: string;
  request_status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED' | 'CANCELLED';
  submitted_at: string;
  decision_at?: string;
  decision_reason?: string;
  allocation_id?: number;
}

export interface MentorAllocation {
  allocation_id: number;
  request_id: number;
  student_user_id: number;
  student_name: string;
  mentor_user_id: number;
  mentor_name: string;
  domain_name?: string;
  allocation_status: 'ACTIVE' | 'COMPLETED' | 'TERMINATED';
  allocated_at: string;
  ended_at?: string;
}

export interface AvailabilitySlot {
  availability_id: number;
  mentor_user_id: number;
  starts_at: string;
  ends_at: string;
  slot_status: 'OPEN' | 'BOOKED' | 'BLOCKED' | 'EXPIRED';
  created_at: string;
}

export interface Booking {
  booking_id: number;
  allocation_id: number;
  availability_id: number;
  booking_type: 'MENTORSHIP' | 'MOCK_INTERVIEW';
  booking_status: 'CONFIRMED' | 'CANCELLED' | 'COMPLETED';
  booked_at: string;
  student_user_id?: number;
  student_name?: string;
  mentor_user_id?: number;
  mentor_name?: string;
  slot_starts_at?: string;
  slot_ends_at?: string;
  session_id?: number;
  session_status?: string;
}

export interface MentorshipSession {
  session_id: number;
  booking_id: number;
  session_status: 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW';
  actual_start_at?: string;
  actual_end_at?: string;
  discussion_summary?: string;
  performance_observations?: string;
  improvement_areas?: string;
  next_steps?: string;
  preparation_recommendation?: string;
  recorded_at?: string;
  student_name?: string;
  mentor_name?: string;
  slot_starts_at?: string;
  slot_ends_at?: string;
  skill_assessments?: { skill_id: number; skill_name: string; assessment_result: string; assessment_notes?: string }[];
}

export interface MentorReview {
  review_id: number;
  session_id: number;
  rating: number;
  rating_label?: string;
  review_text?: string;
  submitted_at: string;
  student_name?: string;
}

export interface NotificationItem {
  notification_id: number;
  recipient_user_id: number;
  channel: string;
  notification_type: string;
  title: string;
  body_text: string;
  is_read: boolean;
  created_at: string;
}

export interface PlatformOverviewStats {
  total_users: number;
  active_students: number;
  active_mentors: number;
  active_allocations: number;
  completed_sessions: number;
  average_mentor_rating: number;
  total_reviews: number;
}

export interface FunnelReport {
  total_requests: number;
  accepted_requests: number;
  confirmed_bookings: number;
  completed_sessions: number;
  reviewed_sessions: number;
  steps: {
    step_name: string;
    count: number;
    conversion_rate_percent: number;
  }[];
}

