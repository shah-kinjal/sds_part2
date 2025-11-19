import { goto } from '$app/navigation';
import { checkIsAuthenticated } from '$lib/auth';

export const ssr = false;

export async function load({ url }) {
	const isAuthenticated = await checkIsAuthenticated();

	const onLoginPage = url.pathname === '/login';

	if (onLoginPage) {
		if (isAuthenticated) {
			await goto('/');
		}
	} else {
		if (!isAuthenticated) {
			await goto('/login');
		}
	}

	return {
		isAuthenticated
	};
}

