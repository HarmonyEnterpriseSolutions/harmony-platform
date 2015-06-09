package gnue.forms.components.table;

import javax.swing.JTable;
import javax.swing.table.*;
import java.awt.event.*;
import java.awt.Cursor;

public class TableColumnFitData extends MouseAdapter {

	
	public void mouseClicked(MouseEvent event) {
		if (event.getButton() == event.BUTTON1 && event.getClickCount() == 2) {
			JTableHeader header = (JTableHeader)event.getSource();
			
			if (header.getCursor().equals(Cursor.getPredefinedCursor(Cursor.E_RESIZE_CURSOR))) {
				
				JTable table = header.getTable();
				TableColumnModel columnModel = table.getColumnModel();
				
				int col = columnModel.getColumnIndexAtX(event.getX());
				if (col < 0) 
					return;
					
				// if user clicked column at the left
				if (col == columnModel.getColumnIndexAtX(event.getX() + columnModel.getColumn(col).getWidth()/2)) {
					col--;
					if (col < 0) 
						return;
				}
				
				updateColumnPreferredWidth(table, col, false);
				
			}
		}
	}
	
	private static final int COLUMN_EXTRA_WIDTH = 5;
	private static final int COLUMN_MIN_WIDTH = 60;

	/**
	 * sets table column preferred size to fit data
	 */
	public static void updateColumnPreferredWidth(JTable table, int col, boolean fixedWidth, int minWidth) {
		
		JTableHeader header = table.getTableHeader();
		TableColumnModel columnModel = table.getColumnModel();
		TableColumn column = columnModel.getColumn(col);
		
		TableModel model = table.getModel();
		
		int headerWidth = header.getDefaultRenderer().getTableCellRendererComponent(
			table, 
			column.getHeaderValue(),
			false, false, 
			-1,	col
		).getPreferredSize().width + COLUMN_EXTRA_WIDTH;
			
		int width = Math.max(minWidth, headerWidth);

		TableCellRenderer renderer = table.getDefaultRenderer(model.getColumnClass(col));
		for (int row = 0; row < table.getRowCount(); row++) {
			int cellWidth = renderer.getTableCellRendererComponent(
				table, 
				model.getValueAt(row, col), 
				false, false, 
				row, col
			).getPreferredSize().width;
			
			width = Math.max(cellWidth,	width - COLUMN_EXTRA_WIDTH) + COLUMN_EXTRA_WIDTH;
		}
	
		if (fixedWidth) {
			column.setMinWidth(0);
			column.setMaxWidth(Integer.MAX_VALUE);
		}
		
		column.setPreferredWidth(width);
		
		if (fixedWidth) {
			column.setMinWidth(width);
			column.setMaxWidth(width);
		}
	}

	/**
	 * sets table column preferred size to fit data
	 */
	public static void updateColumnPreferredWidth(JTable table, int col, boolean fixedWidth) {
		updateColumnPreferredWidth(table, col, fixedWidth, COLUMN_MIN_WIDTH);
	}

}
