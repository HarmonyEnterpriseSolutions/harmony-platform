package gnue.forms.rpc;
import java.io.*;

public class RpcException extends Exception {

	RpcException() {
		super();
	}

	RpcException(Throwable e) {
		super(null, e);
	}

	RpcException(String message, Throwable e) {
		super(message, e);
	}

}
