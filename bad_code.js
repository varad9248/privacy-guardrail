// bad_code.js
function authenticateUser(req, res) {
    const userEmail = req.body.email;
    
    // SECURITY VIOLATION: Hardcoded Slack Token and Stripe Key
    const SLACK_BOT_TOKEN = "xoxb-213456789012-3214567890123-abcde12345fghij67890klmn";
    const STRIPE_LIVE_KEY = "sk_live_51J9xX9L8bABCD1234EFGH5678IJKL90MNOPQ1234RSTUV";

    console.log("Authenticating user: " + userEmail + " with Stripe Key: " + STRIPE_LIVE_KEY);
    
    db.verify(userEmail);
}