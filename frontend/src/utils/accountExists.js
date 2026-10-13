// Did a sign-up attempt hit an email that already has an account?
//
// Supabase answers in two ways, depending on whether "Confirm email" is switched on for the project:
//   * Confirm email OFF: signUp returns an error, "User already registered" (code user_already_exists).
//   * Confirm email ON (the usual setting): to avoid leaking who has an account it returns a normal-looking success, but
//     the returned user has an EMPTY `identities` list. A brand-new (or still-unconfirmed) sign-up has one identity.
// Either way the person should be told to log in instead.
export function isExistingAccount(data, error) {
  if (error) {
    const text = `${error.code ?? ''} ${error.message ?? ''}`.toLowerCase()
    return text.includes('user_already_exists') || text.includes('already registered') || text.includes('already been registered')
  }
  const identities = data?.user?.identities
  return Array.isArray(identities) && identities.length === 0
}

export const EXISTING_ACCOUNT_MESSAGE = 'An account with this email already exists.'
