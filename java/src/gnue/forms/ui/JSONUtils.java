package gnue.forms.ui;
import org.json.*;
import java.lang.reflect.Array;

class JSONUtils {

	public static Object[] jsonArrayToObjectArray(JSONArray a) {
		Object[] array = new Object[a.length()];
		for (int i=0; i<array.length; i++) {
			array[i] = a.get(i);
		}
		return array;
	}

	public static Object jsonArrayToObjectArray(JSONArray a, Class componentType) {
		Object array = Array.newInstance(componentType, a.length());
		for (int i=0; i<a.length(); i++) {
			Array.set(array, i, a.get(i));
		}
		return array;
	}
}
