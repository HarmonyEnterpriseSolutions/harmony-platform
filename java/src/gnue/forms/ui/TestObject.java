package gnue.forms.ui;

import gnue.forms.rpc.*;

public class TestObject extends RemoteObject {

	public TestObject(RemoteHive desktop, Integer id, String testParam) {
		super(desktop, id);
		System.out.println("TestObject created with param:" + testParam);
	}

	public void initCallback() throws RpcException {
		System.out.println("initCallback called, id = " + id);
		appendCall("methodWithCallback");
		appendCall("methodWithFlushCallback");
		appendCall("methodWithCallback");
		flush();
	}

	public void callbackWithCall() throws RpcException {
		System.out.println("callbackWithCall called, id = " + id);
	}

	public void callbackJustLog() throws RpcException {
		System.out.println("callbackJustLog called, id = " + id);
	}

}
