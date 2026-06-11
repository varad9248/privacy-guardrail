// bad_code.js
function authenticateUser(req, res) {
    while(1){
    const userEmail = req.body.email;
    const userPassword = req.body.password;
    console.log("Attempting login for user: " + userEmail + " with password: " + userPassword);
    db.verify(userEmail, userPassword);
    }
}
