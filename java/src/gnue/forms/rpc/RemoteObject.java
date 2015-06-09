package gnue.forms.rpc;

import org.json.*;
import java.util.*;
import java.io.*;

public class RemoteObject {

	final protected RemoteHive hive;
	protected Integer id;


	public RemoteObject(RemoteHive hive, Integer id) {
		this.hive = hive;
		this.id = id;
	}

	public Integer getId() {
		return id;
	}

	/*
	public void appendCallKw(String method, Object[] args, Map kwargs)throws RpcException  {
		hive.appendCall(this.createCall(method, args, kwargs));
	}

	public void callKw(String method, Object[] args, Map kwargs) throws RpcException {
		hive.appendCall(this.createCall(method, args, kwargs));
		hive.flush();
	}
	*/

	public void appendCall(String method, Object... args) {
		try {
			hive.appendCall(this.createCall(method, args));
		}
		catch (RpcException e) {
			hive.printStackTrace(e);
		}
	}

	public Object call(String method, Object... args) {
		try {
			hive.appendCall(this.createCall(method, args));
			return hive.flush();
		}
		catch (RpcException e) {
			hive.printStackTrace(e);
			return null;
		}
	}

	public Object flush() {
		try {
			return hive.flush();
		}
		catch (RpcException e) {
			hive.printStackTrace(e);
			return null;
		}
	}

	public void flushIfPending() {
		if (hive.isPending()) {
			flush();
		}
	}

	public RemoteHive getHive() {
		return hive;
	}

	public String toString() {
		String name = getClass().getName();
		int p = name.lastIndexOf(".");
		if (p >= 0) name = name.substring(p+1);
		return String.format("<%s %d>", name, id);
	}

	public RemoteCall createCall(String method, Object[] args, Map kwargs) {
		return new RemoteCall(this, method, args, kwargs);
	}

	public RemoteCall createCall(String method, Object[] args) {
		return new RemoteCall(this, method, args, RemoteCall.NO_KWARGS);
	}

}
