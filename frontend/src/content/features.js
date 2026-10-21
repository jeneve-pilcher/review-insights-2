// Feature switches (keep in step with backend/features.py). A switched-off feature is not shown or run.
export const FEATURES = {
  aiSummaries: false,
  internetMentions: false,
  operatorBilling: false, // the operator-only Billing panel for ADMIN_EMAILS (locations by email domain, contracts)
  companyPage: false, // the multi-location Company page; managers still switch locations on the dashboard
}
