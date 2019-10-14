/*
 * SonarQube Python Plugin
 * Copyright (C) 2011-2019 SonarSource SA
 * mailto:info AT sonarsource DOT com
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 3 of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */
package org.sonar.python.checks;

import com.sonar.sslr.api.AstNode;
import com.sonar.sslr.xpath.api.AstNodeXPathQuery;
import javax.annotation.CheckForNull;
import org.sonar.check.Rule;
import org.sonar.check.RuleProperty;
import org.sonar.python.IssueLocation;
import org.sonar.plugins.python.api.PythonCheck;
import org.sonar.plugins.python.api.PythonVisitorContext;

@Rule(key = XPathCheck.CHECK_KEY)
public class XPathCheck implements PythonCheck {
  public static final String CHECK_KEY = "XPath";
  private static final String DEFAULT_XPATH_QUERY = "";
  private static final String DEFAULT_MESSAGE = "The XPath expression matches this piece of code";

  @RuleProperty(
    key = "xpathQuery",
    defaultValue = "" + DEFAULT_XPATH_QUERY)
  public String xpathQuery = DEFAULT_XPATH_QUERY;

  @RuleProperty(
    key = "message",
    defaultValue = "" + DEFAULT_MESSAGE)
  public String message = DEFAULT_MESSAGE;

  private AstNodeXPathQuery<Object> query = null;
  private PythonVisitorContext context;

  @CheckForNull
  private AstNodeXPathQuery<Object> query() {
    if (query == null && xpathQuery != null && !xpathQuery.isEmpty()) {
      try {
        query = AstNodeXPathQuery.create(xpathQuery);
      } catch (RuntimeException e) {
        throw new IllegalStateException("Unable to initialize the XPath engine, perhaps because of an invalid query: " + xpathQuery, e);
      }
    }
    return query;
  }

  public void scanFile(PythonVisitorContext context) {
    this.context = context;
    AstNode tree = context.rootAstNode();
    if (tree != null) {
      visitFile(tree);
    }
  }

  private  void visitFile(AstNode fileNode) {
    AstNodeXPathQuery<Object> compiledQuery = query();
    if (compiledQuery != null) {
      compiledQuery.selectNodes(fileNode).forEach(this::reportIssue);
    }
  }

  private void reportIssue(Object object) {
    if (object instanceof AstNode) {
      addIssue((AstNode) object, message);
    } else if (object instanceof Boolean && (Boolean) object) {
      addFileIssue(message);
    }
  }

  private void addIssue(AstNode node, String message) {
    PreciseIssue newIssue = new PreciseIssue(this, IssueLocation.preciseLocation(node, message));
    context.addIssue(newIssue);
  }

  private void addFileIssue(String message) {
    PreciseIssue newIssue = new PreciseIssue(this, IssueLocation.atFileLevel(message));
    context.addIssue(newIssue);
  }

}
