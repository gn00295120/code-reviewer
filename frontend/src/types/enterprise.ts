export interface AuditLog {
  id: string;
  action: string;
  actor: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  ip_address: string;
  created_at: string;
}

export interface SecurityPolicy {
  id: string;
  name: string;
  policy_type: "rate_limit" | "secret_detection" | "access_control";
  config: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}
