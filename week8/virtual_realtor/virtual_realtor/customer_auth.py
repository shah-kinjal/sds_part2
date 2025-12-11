from constructs import Construct
import aws_cdk.aws_cognito as cognito

class CustomerAuth(Construct):
    user_pool: cognito.UserPool
    client: cognito.UserPoolClient

    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        self.user_pool = cognito.UserPool(
            self,
            "CustomerUserPool",
            user_pool_name="vr-customer-user-pool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            # Email is required by default if it's an alias, but let's be explicit if needed
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True)
            ),
            sign_in_policy=cognito.SignInPolicy(
                allowed_first_auth_factors=cognito.AllowedFirstAuthFactors(password=True, email_otp=True),
            ),
            # No password policy needed if password is false, but good to keep defaults
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
        )

        self.client = self.user_pool.add_client(
            "CustomerUserPoolClient",
            auth_flows=cognito.AuthFlow(
                user=True,      # Enables USER_AUTH for email OTP
                custom=True,    # Good to have if we need custom flows later
                user_srp=True   # Standard secure remote password if needed
            ),
            # No client secret for public frontend
            generate_secret=False,
            supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
        )
