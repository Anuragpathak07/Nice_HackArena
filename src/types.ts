export type Risk = 'LOW' | 'MEDIUM' | 'HIGH';
export type Status = 'PENDING' | 'IN_REVIEW' | 'APPROVED' | 'REJECTED';
export interface Finding { field: string; status: string; reason: string }
export interface Identity { name_on_id: string; dob_on_id: string; address_on_id: string }
export interface Match { screening_id: string; name: string; country: string; match_score: number; match_type: string; reason: string; watchlist_reason: string; review_status: string; reviewed_by: string | null }
export interface Applicant {
  application_id: string; full_name: string; dob: string; address: string; id_number: string;
  occupation: string; annual_income: number; country: string; status: Status; risk_level: Risk;
  created_at: string; discrepancy_count: number; unverified_count: number; checks: Finding[];
  watchlist_matches: number; highest_match: number; passed: boolean; identity?: Identity | null; matches?: Match[];
}
export interface WatchEntry { watchlist_id: string; name: string; country: string; reason: string; created_at: string }
export interface Audit { audit_id: string; application_id: string; action: string; old_status: string | null; new_status: string | null; performed_by: string; timestamp: string; reason: string }
export interface Onboarding { full_name: string; dob: string; address: string; id_number: string; occupation: string; annual_income: number; country: string; identity: Identity | null }
