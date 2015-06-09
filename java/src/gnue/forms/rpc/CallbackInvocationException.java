package gnue.forms.rpc;

public class CallbackInvocationException extends RpcException {

	CallbackInvocationException(Throwable e) {
		super(e);
	}

	CallbackInvocationException(String message, Throwable e) {
		super(message, e);
	}
}
