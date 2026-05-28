// bad_code.js
function authenticateUser(req, res) {
    const userEmail = req.body.email;
    
    // SECURITY VIOLATION: Hardcoded AWS Credential and PII Logging
    const AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE";
    const AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";

    console.log("Authenticating user: " + userEmail + " with AWS Key: " + AWS_ACCESS_KEY_ID);
    
    db.verify(userEmail);
}