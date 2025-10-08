export interface Thread {
  id: string;
  flow_id: string;
  status: string;
  started_at: string;
  closed_at?: string | null;
}
