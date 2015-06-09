package gnue.forms.rpc;
import org.json.*;

/**
 * JSON RPC 1.0 error
 */
public class JSONRpcException extends JSONException {

	Object error;

	/**
	 * Method JSONRPCError
	 *
	 *
	 */
	public JSONRpcException(Object error) {
		super(error.toString());
		this.error = error;
	}
}
