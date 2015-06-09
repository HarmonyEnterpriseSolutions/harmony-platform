package gnue.forms.components;

/**
 * @(#)SingleSelectionListComponent.java
 *
 *
 * @author 
 * @version 1.00 2010/2/18
 */

import javax.swing.*;
import javax.swing.event.*;


public interface SingleSelectionListComponent {
 
	public ListModel getListModel();
	public SingleSelectionModel getSelectionModel();
    
}