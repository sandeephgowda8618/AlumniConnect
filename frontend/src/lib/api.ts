import {
  User, StudentProfile, MentorProfile, RecommendedMentor,
  MentorshipRequest, MentorAllocation, AvailabilitySlot,
  Booking, MentorshipSession, MentorReview, NotificationItem,
  PlatformOverviewStats, FunnelReport, Skill, MentorshipDomain,
  Department, Company
} from '../types';

const API_BASE = (typeof window !== 'undefined')
  ? (process.env.NEXT_PUBLIC_API_URL && !process.env.NEXT_PUBLIC_API_URL.includes('localhost:8000') ? process.env.NEXT_PUBLIC_API_URL : '/api/v1')
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1');

class ApiClient {
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('ac_token');
  }

  public setToken(token: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('ac_token', token);
    }
  }

  public clearAuth() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('ac_token');
      localStorage.removeItem('ac_user');
    }
  }

  public getStoredUser(): User | null {
    if (typeof window === 'undefined') return null;
    const str = localStorage.getItem('ac_user');
    if (!str) return null;
    try {
      return JSON.parse(str);
    } catch {
      return null;
    }
  }

  public setStoredUser(user: User) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('ac_user', JSON.stringify(user));
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      this.clearAuth();
      if (typeof window !== 'undefined' && 
          !window.location.pathname.includes('/login') && 
          !window.location.pathname.includes('/register') && 
          !window.location.pathname.includes('/student/mentors') && 
          window.location.pathname !== '/') {
        window.location.href = '/login';
      }
      throw new Error('Unauthorized or session expired');
    }

    if (!res.ok) {
      let detail = `Request failed with status ${res.status}`;
      try {
        const errJson = await res.json();
        detail = errJson.detail || detail;
      } catch {}
      throw new Error(detail);
    }

    return res.json();
  }

  // --- Auth ---
  async login(email: string, password: string):Promise<User> {
    const res = await this.request<User>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (res.access_token) {
      this.setToken(res.access_token);
      this.setStoredUser(res);
    }
    return res;
  }

  async registerStudent(data: any): Promise<User> {
    const res = await this.request<User>('/auth/register/student', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (res.access_token) {
      this.setToken(res.access_token);
      this.setStoredUser(res);
    }
    return res;
  }

  async registerMentor(data: any): Promise<User> {
    const res = await this.request<User>('/auth/register/mentor', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (res.access_token) {
      this.setToken(res.access_token);
      this.setStoredUser(res);
    }
    return res;
  }

  // --- Catalogues ---
  async getSkills(): Promise<Skill[]> {
    return this.request<Skill[]>('/catalogues/skills');
  }

  async getDomains(): Promise<MentorshipDomain[]> {
    return this.request<MentorshipDomain[]>('/catalogues/domains');
  }

  async getDepartments(): Promise<Department[]> {
    return this.request<Department[]>('/catalogues/departments');
  }

  async getCompanies(): Promise<Company[]> {
    return this.request<Company[]>('/catalogues/companies');
  }

  // --- Student Portal ---
  async getStudentProfile(): Promise<StudentProfile> {
    return this.request<StudentProfile>('/students/profile');
  }

  async updateStudentProfile(data: Partial<StudentProfile>): Promise<StudentProfile> {
    return this.request<StudentProfile>('/students/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async syncStudentSkillsAndDomains(data: {
    skills: { skill_id: number; proficiency_level?: string; years_experience?: number }[];
    domains: { domain_id: number; priority_order?: number; interest_notes?: string }[];
  }): Promise<StudentProfile> {
    return this.request<StudentProfile>('/students/skills-and-domains', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async addStudentSkill(data: {
    skill_id: number;
    proficiency_level: string;
    years_experience?: number;
  }): Promise<any> {
    return this.request('/students/skills', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async removeStudentSkill(skillId: number): Promise<void> {
    return this.request(`/students/skills/${skillId}`, {
      method: 'DELETE',
    });
  }

  async addStudentDomain(data: {
    domain_id: number;
    priority_order: number;
    interest_notes?: string;
  }): Promise<any> {
    return this.request('/students/domains', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async removeStudentDomain(domainId: number): Promise<void> {
    return this.request(`/students/domains/${domainId}`, {
      method: 'DELETE',
    });
  }

  async discoverRecommendations(filters: any = {}): Promise<{ results: RecommendedMentor[] }> {
    return this.request<{ results: RecommendedMentor[] }>('/recommendations/discover', {
      method: 'POST',
      body: JSON.stringify(filters),
    });
  }

  async submitMentorshipRequest(data: {
    mentor_user_id: number;
    domain_id: number;
    request_message: string;
    career_goal_snapshot?: string;
  }): Promise<MentorshipRequest> {
    return this.request<MentorshipRequest>('/requests', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getStudentRequests(): Promise<MentorshipRequest[]> {
    return this.request<MentorshipRequest[]>('/requests/student');
  }

  async getStudentAllocations(): Promise<MentorAllocation[]> {
    return this.request<MentorAllocation[]>('/allocations/student');
  }

  async getStudentBookings(): Promise<Booking[]> {
    return this.request<Booking[]>('/bookings/student');
  }

  async getStudentSessions(): Promise<MentorshipSession[]> {
    return this.request<MentorshipSession[]>('/sessions/student');
  }

  // --- Mentor Portal ---
  async getMentorProfile(): Promise<MentorProfile> {
    return this.request<MentorProfile>('/mentors/profile');
  }

  async updateMentorProfile(data: Partial<MentorProfile>): Promise<MentorProfile> {
    return this.request<MentorProfile>('/mentors/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async getMentorInbox(): Promise<MentorshipRequest[]> {
    return this.request<MentorshipRequest[]>('/requests/mentor/inbox');
  }

  async acceptRequest(requestId: number): Promise<MentorAllocation> {
    return this.request<MentorAllocation>(`/requests/${requestId}/accept`, {
      method: 'POST',
    });
  }

  async rejectRequest(requestId: number, reason: string): Promise<MentorshipRequest> {
    return this.request<MentorshipRequest>(`/requests/${requestId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ decision: 'REJECT', decision_reason: reason }),
    });
  }

  async getMentorSlots(): Promise<AvailabilitySlot[]> {
    return this.request<AvailabilitySlot[]>('/availability/mentor');
  }

  async getOpenSlotsForMentor(mentorId: number): Promise<AvailabilitySlot[]> {
    return this.request<AvailabilitySlot[]>(`/availability/mentor/${mentorId}/open`);
  }

  async publishAvailabilitySlot(data: { starts_at: string; ends_at: string }): Promise<AvailabilitySlot> {
    return this.request<AvailabilitySlot>('/availability', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMentorSessions(): Promise<MentorshipSession[]> {
    return this.request<MentorshipSession[]>('/sessions/mentor');
  }

  async recordSessionOutcome(sessionId: number, data: any): Promise<MentorshipSession> {
    return this.request<MentorshipSession>(`/sessions/${sessionId}/outcome`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // --- Bookings & Reviews ---
  async createBooking(data: {
    availability_id: number;
    allocation_id: number;
    booking_type: string;
    idempotency_key?: string;
  }): Promise<Booking> {
    return this.request<Booking>('/bookings', {
      method: 'POST',
      body: JSON.stringify({
        ...data,
        idempotency_key: data.idempotency_key || `idem-${Date.now()}-${data.availability_id}`,
      }),
    });
  }

  async cancelBooking(bookingId: number, reason: string): Promise<Booking> {
    return this.request<Booking>(`/bookings/${bookingId}/cancel`, {
      method: 'PUT',
      body: JSON.stringify({ reason }),
    });
  }

  async submitMentorReview(data: {
    session_id: number;
    rating: number;
    review_text?: string;
  }): Promise<MentorReview> {
    return this.request<MentorReview>('/reviews/mentor-review', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // --- Notifications ---
  async getNotifications(unreadOnly: boolean = false): Promise<NotificationItem[]> {
    return this.request<NotificationItem[]>(`/notifications/?unread_only=${unreadOnly}`);
  }

  async markNotificationRead(notificationId: number): Promise<void> {
    await this.request(`/notifications/${notificationId}/read`, { method: 'PUT' });
  }

  // --- Admin Analytics ---
  async getPlatformOverview(): Promise<PlatformOverviewStats> {
    return this.request<PlatformOverviewStats>('/analytics/overview');
  }

  async getFunnelReport(): Promise<FunnelReport> {
    return this.request<FunnelReport>('/analytics/funnel');
  }

  async getCapacityReport(): Promise<any[]> {
    return this.request<any[]>('/analytics/capacity-utilization');
  }

  async getDemandSupply(): Promise<any[]> {
    return this.request<any[]>('/analytics/demand-supply');
  }

  async getAuditLogs(): Promise<any[]> {
    return this.request<any[]>('/admin/audit-logs');
  }
}

export const api = new ApiClient();

