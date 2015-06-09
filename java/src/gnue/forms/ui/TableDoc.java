package gnue.forms.ui;

/**
 * @(#)TableModel.java
 *
 *
 * @author
 * @version 1.00 2009/3/19
 */
import javax.swing.table.*;
import org.json.*;
import java.util.List;
import java.util.ArrayList;
import java.util.Iterator;
import javax.swing.*;

public class TableDoc extends AbstractTableModel {

	//private final static String[] COLUMN_ORDER_SUFFIX = new String[]{" \u25b2", "", " \u25bc"};
	private final static String[] COLUMN_ORDER_PREFIX = new String[]{"\u2191 ", "", "\u2193 "};

	JSONObject[] columns;
	String[] flags;
	List<Class> columnClasses = new ArrayList<Class>();
	List<Object[]> data = new ArrayList<Object[]>();

	public TableDoc() {
	}

	public void setColumns(JSONArray flags, JSONArray columns) {
		this.flags   = (String	  [])JSONUtils.jsonArrayToObjectArray(flags,	   String.class);
		this.columns = (JSONObject[])JSONUtils.jsonArrayToObjectArray(columns, JSONObject.class);

		// insert booleans classes for flags
		for (int i=0; i<this.flags.length; i++) {
			columnClasses.add(0, Boolean.class);
		}

		fireTableStructureChanged();
	}
	
	public void setData(JSONArray data, JSONArray columns) {
		//System.out.printf(">>> setData %s\n", data.length());
		this.data.clear();
		for (int i=0; i<data.length(); i++) {
			this.data.add(JSONUtils.jsonArrayToObjectArray(data.getJSONArray(i)));
		}
		// update columns
		for (int i=0; i<columns.length(); i++) {
			JSONObject column = columns.getJSONObject(i);
			for (Iterator keys = column.keys(); keys.hasNext(); ) {
				String key = (String)keys.next();				
				this.columns[i].put(key, column.get(key));
			}
		}
		fireTableDataChanged();
	}

	public void setRowData(Integer row, JSONArray rowData) {
		//System.out.printf(">>> setRowData %s\n", row);
		this.data.set(row, JSONUtils.jsonArrayToObjectArray(rowData));
		fireTableRowsUpdated(row, row);
	}

	//////////////////////////////////////////////////////
	//
	public Class getColumnClass(int col) {
		if (col == 0) {
			return Integer.class;
		}
		else {
			col--;
			return columnClasses.get(col);
		}
	}

	public int getColumnCount() {
		if (columns != null)
			return columns.length + 1;
		else
			return 1;
	}

	public String getColumnName(int col) {
		if (col == 0) {
			return "";
		}
		else {
			col--;
			if (columns != null) {
				return COLUMN_ORDER_PREFIX[columns[col].optInt("order", 0)+1] + columns[col].getString("label");
			}
			else {
				return "";
			}
		}
	}

	public String getColumnTip(int col) {
		if (col == 0) {
			return "";
		}
		else {
			col--;
			if (columns != null) {
				return COLUMN_ORDER_PREFIX[columns[col].optInt("order", 0)+1] + columns[col].getString("tip");
			}
			else {
				return "";
			}
		}
	}

	public int getRowCount() {
		return data.size();
	}

	public Object getValueAt(int row, int col) {
		if (col == 0) {
			return row + 1;
		}
		else {
			col--;
			Object value = data.get(row)[col];
			//System.out.printf(">>> getValueAt %s, %s: %s\n", row, col, value);
			return value;
		}
	}

	public boolean isCellEditable(int row, int col) {
		if (col == 0) {
			return false;
		}
		else {
			col--;
			return columns[col].getBoolean("editable");
		}
	}

	public void setValueAt(Object aValue, int row, int col) {
		// TODO
	}

	/////////////////////////////////////////////////
	
	public void addColumnClass(Class c) {
		//System.out.printf(">>> addColumnClass %s\n", c);
		columnClasses.add(c);
	}

}
