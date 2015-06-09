package gnue.forms.rpc;

import java.net.CookiePolicy;
import java.net.URI;
import java.net.HttpCookie;


public class RpcCookiePolicy implements CookiePolicy {
	public boolean shouldAccept(URI uri, HttpCookie cookie) {
		//String host = uri.getHost();
		//return host.equals("localhost");
		return true;
	}
}