package gnue.forms.rpc;

import java.util.*;
import org.json.*;

public class RemoteCall {

	public static final Object[] NO_ARGS = new Object[] {};
	public static final Map NO_KWARGS = new HashMap();

	private RemoteObject object;
	private String method;
	private Object[] args;
	private Map kwargs;

	RemoteCall(RemoteObject object, String method, Object[] args, Map kwargs) {
		this.object = object;
		this.method = method;
		this.args   = args;
		this.kwargs = kwargs;
	}

	public void append() throws RpcException {
		object.getHive().appendCall(this);
	}

	public String toString() {
		StringBuffer s = new StringBuffer();
		for (Object arg : args) {
			s.append(", ");
			s.append(arg);
		}
		// TODO: kwargs
		return object.toString() + "." + method + "(" + (s.length() >= 2 ? s.substring(2) : "") + ")";
	}

	public JSONArray toJSON() throws JSONException {
		return new JSONArray(new Object[]{
			object.getId(),
			method,
			argsToJSON(args),
			new JSONObject(kwargs)
		});
	}

	static protected JSONArray argsToJSON(Object[] args) throws JSONException {
		JSONArray ret = new JSONArray();
		for (Object arg: args) {
			if (arg instanceof RemoteObject) {
				JSONObject o = new JSONObject();
				o.put("__roid__", ((RemoteObject)arg).getId());
				ret.put(o);
			}
			else {
				ret.put(arg);
			}
		}
		return ret;
	}

}
