import { Amplify } from 'aws-amplify';
import { signIn, signOut, fetchAuthSession, getCurrentUser } from '@aws-amplify/auth';

let configured = false;

export async function configureAmplify() {
	if (configured) {
		return;
	}
	// @ts-ignore
	const { env } = await import(`${''}/_app/env.js`);
	const userPoolId = env.PUBLIC_VITE_COGNITO_USER_POOL_ID;
	const userPoolClientId = env.PUBLIC_VITE_COGNITO_USER_POOL_CLIENT_ID;
	console.log(
		'Configuring Amplify with User Pool ID:',
		userPoolId,
		'and Client ID:',
		userPoolClientId
	);
	Amplify.configure({
		Auth: {
			Cognito: {
				userPoolId: userPoolId,
				userPoolClientId: userPoolClientId
			}
		}
	});
	configured = true;
}

export async function checkIsAuthenticated(): Promise<boolean> {
	await configureAmplify();
	try {
		// Using forceRefresh: false to use cached session if available.
		// This is faster and avoids unnecessary network requests.
		const session = await fetchAuthSession({ forceRefresh: false });
		return !!session.tokens?.idToken;
	} catch (error) {
		return false;
	}
}

export async function signInWithPassword(username: string, password: string): Promise<boolean> {
	await configureAmplify();
	try {
		const output = await signIn({
			username,
			password
		});
		console.log('Sign in output:', output);
		return output.isSignedIn;
	} catch (error) {
		console.error('Error signing in:', error);
		throw error;
	}
}

export async function signOutUser() {
	await configureAmplify();
	try {
		await signOut();
	} catch (error) {
		console.error('Error signing out:', error);
	}
}

export async function getUsername(): Promise<string | null> {
	await configureAmplify();
	try {
		const user = await getCurrentUser();
		return user.username;
	} catch (error) {
		return null;
	}
}

