package gnue.forms.rpc;

import org.json.*;
import java.net.*;
import java.util.*;
import java.io.*;


public class JSONHttpService extends UrlPoster {

	static int idCounter = 0;
	private final static boolean DEBUG = false;
	protected boolean debug;

	public JSONHttpService(URL url, boolean debug) {
		super(url, new String[][]{
			new String[] {"Content-Type", "application/json"},
			new String[] {"Accept", "application/json"},
		});
		this.debug = debug;
	}

	public Object call(String method, JSONArray args) throws JSONException {
		try {
			Map<String, Object> request = new Hashtable<String, Object>();
			request.put("version", "1.1");
			request.put("id", new Integer(++idCounter));
			request.put("method", method);
			request.put("params", args);
			String r = new JSONObject(request).toString();
			if (debug) System.out.println("REQUEST: " + r);
			Reader response = openTextStream(r);

			JSONTokener tokener;

			if (debug && DEBUG) {
				BufferedReader brResp = new BufferedReader(response);
				StringBuffer bResp = new StringBuffer();
				String line = brResp.readLine();
				while (line != null) {
					bResp.append(line);
					line = brResp.readLine();
				}
				String text = bResp.toString();
				if (debug) System.out.println("\tRESPONSE: " + text);
				tokener = new JSONTokener(text);
			}
			else {
				tokener = new JSONTokener(response);
			}

			JSONObject jResponse = new JSONObject(tokener);

			if (jResponse.has("error")) {
				Object error = jResponse.get("error");
				if (error != null)
					throw new JSONRpcException(error);
			}

			return jResponse.get("result");
		}
		catch (IOException e) {
			throw new JSONException(e);
		}
	}
}
