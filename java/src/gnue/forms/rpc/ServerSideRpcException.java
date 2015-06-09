package gnue.forms.rpc;
import java.io.*;

public class ServerSideRpcException extends RpcException {

	ServerSideRpcException(Throwable e) {
		super(null, e);
	}

	public void printStackTrace(PrintWriter out) {
		out.println(this.getCause().getMessage());
	}

	public void printStackTrace(PrintStream out) {
		out.println(this.getCause().getMessage());
	}

	public void printStackTrace() {
		System.err.println(this.getCause().getMessage());
	}
	
	public String getMessage() {
		return this.getCause().getMessage();
	}
}
