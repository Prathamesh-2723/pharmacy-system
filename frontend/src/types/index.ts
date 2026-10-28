export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "owner" | "pharmacist" | "staff";
  tenant_id: string;
  tenant_name: string;
  tenant_slug: string;
}

export interface DistributorRuleConfig {
  return_window_start_days_before_expiry: number;
  return_window_end_days_before_expiry: number;
  excluded_categories: string[];
  requires_prior_authorization: boolean;
  return_format: string;
  pickup_days: string[];
  credit_note_sla_days: number;
  min_return_value: number;
}

export interface DistributorScorecard {
  id: string;
  name: string;
  code?: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
  active_rule?: DistributorRuleConfig;
  active_returns_count: number;
  total_returned_value: number;
  avg_credit_turnaround_days: number;
  rejection_rate_percent: number;
}

export interface BatchItem {
  id: string;
  product_id: string;
  product_name: string;
  category: string;
  distributor_id: string;
  distributor_name: string;
  batch_no: string;
  expiry_date: string;
  initial_qty: number;
  current_qty: number;
  purchase_price: number;
  mrp?: number;
  invoice_ref?: string;
  status: string;
  value_at_risk: number;
  urgency_bucket: "EXPIRED" | "15D" | "30D" | "60D" | "90D" | "FUTURE";
  eligible: boolean;
  window_opens_on: string;
  window_closes_on: string;
  days_to_window_close: number;
  days_to_expiry: number;
  blocked_reason?: string;
  priority_score: number;
  window_closing_soon: boolean;
}

export interface ReturnRequestItem {
  id: string;
  batch_id: string;
  product_name: string;
  category: string;
  batch_no: string;
  expiry_date: string;
  requested_qty: number;
  accepted_qty?: number;
  unit_purchase_price: number;
  total_value: number;
  reason: string;
}

export interface ReturnStatusEvent {
  id: string;
  from_status?: string;
  to_status: string;
  trigger: string;
  triggered_by?: string;
  comment?: string;
  created_at: string;
}

export interface ReturnRequest {
  id: string;
  return_request_no: string;
  distributor_id: string;
  distributor_name: string;
  distributor_phone?: string;
  status: "DRAFT" | "APPROVED" | "SENT" | "ACKNOWLEDGED" | "PICKED_UP" | "CREDIT_ISSUED" | "SETTLED" | "REJECTED" | "DISPUTED";
  total_estimated_value: number;
  total_credit_received: number;
  item_count: number;
  approved_at?: string;
  dispatched_at?: string;
  credit_sla_deadline?: string;
  created_at: string;
  items: ReturnRequestItem[];
  events: ReturnStatusEvent[];
}

export interface CreditNote {
  id: string;
  distributor_id: string;
  distributor_name: string;
  return_request_id?: string;
  return_request_no?: string;
  credit_note_no: string;
  credit_note_date: string;
  expected_amount: number;
  credited_amount: number;
  shortfall_amount: number;
  status: "MATCHED" | "PARTIAL" | "DISPUTED";
  remarks?: string;
  created_at: string;
}

export interface DashboardKpis {
  value_expiring_15d: number;
  value_expiring_30d: number;
  value_expiring_60d: number;
  value_expiring_90d: number;
  total_value_at_risk: number;
  returns_pending_count: number;
  returns_pending_value: number;
  overdue_credits_count: number;
  overdue_credits_value: number;
  writeoffs_avoided_month: number;
  reconciliation_accuracy_percent: number;
}
