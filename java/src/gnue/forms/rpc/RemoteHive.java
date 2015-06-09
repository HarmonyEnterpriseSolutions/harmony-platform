package gnue.forms.rpc;

import org.json.*;
import java.util.*;

public class RemoteHive {

	String[] packages;
	JSONHttpService service;
	List<JSONArray> calls = new Vector<JSONArray>();
	Long id;
	Map<Integer, RemoteObject> objects = new Hashtable<Integer, RemoteObject>();
	Map<Class, Class> simpleTypes = new Hashtable<Class, Class>();
	protected boolean debug;

	public RemoteHive(String[] packages, JSONHttpService service, boolean debug) {
		this.id = Calendar.getInstance().getTimeInMillis();
		this.packages = packages;
		this.service = service;
		this.debug = debug;

		//simpleTypes.put(Boolean.class, boolean.class);
		//simpleTypes.put(Integer.class, int.class);
		//simpleTypes.put(Long.class,	 long.class);
		//simpleTypes.put(Float.class,   float.class);
	}

	public void addClassTranslation(Class from, Class to) {
		simpleTypes.put(from, to);
	}

	protected Class findClass(String type) throws ClassNotFoundException {
		for (String p : packages) {
			try {
				return Class.forName(p + "." + type);
			}
			catch (ClassNotFoundException e) {
				printStackTrace(e);
			}
		}
		throw new ClassNotFoundException(type);
	}

	protected RemoteObject createObject(String type, Integer id, JSONArray args) throws JSONException, ClassNotFoundException, NoSuchMethodException, InstantiationException, IllegalAccessException, java.lang.reflect.InvocationTargetException {
		if (debug) System.out.println("Creating object: " + type + ", " + id + ", " + args);

		Class[]  tArgs = new Class [args.length() + 2];
		Object[] oArgs = new Object[args.length() + 2];

		tArgs[0] = this.getClass();
		tArgs[1] = Integer.class;

		oArgs[0] = this;
		oArgs[1] = id;

		for (int i=0; i<args.length(); i++) {
			tArgs[i+2] = args.get(i).getClass();
			oArgs[i+2] = args.get(i);
		}
		// InstantiationException without cause means that class is abstract
		RemoteObject object = (RemoteObject)findClass(type).getConstructor(tArgs).newInstance(oArgs);
		objects.put(id, object);
		return object;
	}

	RemoteObject getObject(Integer id) {
		return (RemoteObject)objects.get(id);
	}

	Object resolveObject(Object o) throws JSONException {
		if (o instanceof JSONArray) {
			return resolveJSONArray((JSONArray)o);
		}
		else if (o instanceof JSONObject) {
			return resolveJSONObject((JSONObject)o);
		}
		else {
			return o;
		}
	}

	JSONArray resolveJSONArray(JSONArray a) throws JSONException {
		for (int i=0; i<a.length(); i++) {
			a.put(i, resolveObject(a.get(i)));
		}
		return a;
	}

	Object resolveJSONObject(JSONObject o) throws JSONException {
		if (o.length() == 1 && o.has("__roid__")) {
			return getObject(new Integer(o.getInt("__roid__")));
		}
		else {
			return o;
		}
	}



	/**
	 * Remote call
	 */
	public void appendCall(RemoteCall call) throws RpcException {
		try {
			calls.add(call.toJSON());
		}
		catch (JSONException e) {
			throw new RpcException(e);
		}
	}

	public boolean isPending() {
		return calls.size() > 0;
	}

	/**
	 * flushes until server callbacks left
	 */
	public Object flush() throws RpcException {
		try {
			Object returnValue = null;
			JSONArray response;
			do {
				JSONArray jCalls = new JSONArray(calls);
				calls.clear();
				response = (JSONArray)service.call("process", new JSONArray(new Object[]{id, jCalls}));

				// response is [<calbacks>, <calls left>, <return value of last call if any>]

				if (jCalls.length() > 0) {
					// return value will be return of last call
					returnValue = response.get(2);
				}

				JSONArray callbacks = response.getJSONArray(0);

				for (int i=0; i<callbacks.length(); i++) {
					JSONArray callback = callbacks.getJSONArray(i);

					Integer id	   = new Integer(callback.getInt(0));
					String method  = callback.getString(1);
					JSONArray args = resolveJSONArray(callback.getJSONArray(2));

					if (method.startsWith("new ")) {
						String constructor = method.substring(4);
						createObject(constructor, id, args);
					}
					else {
						Class[]  tArgs = new Class [args.length()];
						Object[] oArgs = new Object[args.length()];

						for (int j=0; j<args.length(); j++) {
							Object arg = args.get(j);
							Class tArg = arg.getClass();
							Class tArgSimple = (Class)simpleTypes.get(tArg);
							if (tArgSimple != null) {
								tArg = tArgSimple;
							}
							tArgs[j] = tArg;
							oArgs[j] = arg;
						}

						RemoteObject object = objects.get(id);
						if (object == null)
							throw new AssertionError("Object not in cache with id = " + id);

						if (debug) System.out.println("Calling " + object.createCall(method, oArgs));
						object.getClass().getMethod(method, tArgs).invoke(object, oArgs);
					}
				}
			}
			while (response.getInt(1) > 0);
			return returnValue;
		}
		catch (JSONRpcException e) {
			// has overrided printstacktrace, prints message only
			throw new ServerSideRpcException(e);
		}
		catch (JSONException e) {
			throw new RpcException(e);
		}
		catch (ClassNotFoundException e) {
			throw new CallbackInvocationException(e);
		}
		catch (NoSuchMethodException e) {
			throw new CallbackInvocationException(e);
		}
		catch (InstantiationException e) {
			throw new CallbackInvocationException(e);
		}
		catch (IllegalAccessException e) {
			throw new CallbackInvocationException(e);
		}
		catch (java.lang.reflect.InvocationTargetException e) {
			throw new CallbackInvocationException(e);
		}
	}
	
	public void printStackTrace(Throwable e) {
		e.printStackTrace();
	}
	
	/**
	 * drop all objects
	 */
	public void reset() {
		objects.clear();
	}
	

}
